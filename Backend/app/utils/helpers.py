import logging
import time
import random

from flask import jsonify
from newspaper import article
from googlenewsdecoder import new_decoderv1
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import re
from rapidfuzz import process, fuzz
# spacy moved to news-processor microservice - not needed in backend API
# import spacy
from .helpers_constants import (
    sp500_plus2_dict,
    SECTOR_KEYWORDS,
    country_to_region,
    regions,
)
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

load_dotenv()

# LAZY LOADING: Defer heavy imports and initialization
_nlp = None
_sp500_plus2 = None


def _get_nlp():
    """Lazy load spaCy model (500MB+) only when needed."""
    global _nlp
    if _nlp is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Loading spaCy en_core_web_trf model (first use)...")
        import spacy
        _nlp = spacy.load("en_core_web_trf")
        logger.info("spaCy model loaded successfully")
    return _nlp


def _get_sp500_dataframe():
    """Lazy load pandas DataFrame only when needed."""
    global _sp500_plus2
    if _sp500_plus2 is None:
        import pandas as pd
        _sp500_plus2 = pd.DataFrame.from_dict(sp500_plus2_dict)
    return _sp500_plus2


# Add to the dictionary
for region in regions:
    country_to_region[region] = region


# spaCy model moved to news-processor microservice
# nlp = spacy.load("en_core_web_trf")

# Get S&P 500 tickers from Wikipedia
# url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
# tables = pd.read_html(url)
# sp500_df = tables[0]

# Get only the necessary columns
# sp500_plus2 = sp500_df[["Security", "GICS Sector"]]

# Define new rows as DataFrames
# new_row_1 = pd.DataFrame([{"Security": "HSBC Holdings plc", "GICS Sector": "Financials"}])
# new_row_2 = pd.DataFrame([{"Security": "Taiwan Semiconductor Manufacturing Company Limited", "GICS Sector": "Information Technology"}])

# Concatenate the new rows
# sp500_plus2 = pd.concat([sp500_plus2, new_row_1, new_row_2], ignore_index=True)

# Create list of known companies (lazy loaded)
def get_known_companies():
    return _get_sp500_dataframe()["Security"].tolist()


known_companies = None  # Will be populated lazily


# Create list of unique GICS sectors (lazy loaded)
def get_sectors():
    return _get_sp500_dataframe()["GICS Sector"].unique().tolist()


sectors = None  # Will be populated lazily


# ** General-purpose helper functions for common tasks like formatting responses or handling dates.


def format_response(data, message="Success", status_code=200):
    return (
        jsonify({"status": status_code, "message": message, "data": data}),
        status_code,
    )


def calculate_percentage(part, whole):
    if whole == 0:
        return 0
    return (part / whole) * 100


def password_rule_checker(password):
    # Check if password is at least 8 characters long
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    # Check if password has at least one uppercase letter
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    # Check if password has at least one lowercase letter
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    # Check if password has at least one digit
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    # Check if password has at least one special character
    if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/~" for char in password):
        return False, "Password must contain at least one special character"
    return True, "Password meets all requirements"


def format_date_into_tuple_for_gnews(date):
    date = date.split("-")
    return (int(date[0]), int(date[1]), int(date[2]))


def URL_decoder(url):
    # Decode the URL
    try:
        decoded_url = new_decoderv1(url)
        if decoded_url.get("status"):
            return decoded_url
        else:
            print("Error:", decoded_url["message"])
    except Exception as e:
        print(f"Error occurred: {e}")


def get_article_details(url, article_html, news_id=None):
    from app.services.sentiment_analysis import (
        get_sentiment,
    )  # Move import here to avoid circular import

    try:
        # Fetch the article details
        article_result = article(url, input_html=article_html)
        article_result.nlp()

        # Log extracted text length for debugging
        text_length = len(article_result.text) if article_result.text else 0
        logging.info(f"📰 Extracted article text: {text_length} chars from {url}")

        # Early check: if text extraction failed, return immediately
        if not article_result.text or text_length < 100:
            logging.error(f"✗ Article text extraction failed or too short ({text_length} chars) - aborting processing")
            return None

        # Summarize and extract entities from the article text
        interpreted_news = news_interpreter(article_result.text, 100)

        # If news_interpreter returned None, article is invalid
        if not interpreted_news:
            logging.error(f"✗ Article validation failed for {url} - aborting processing")
            return None

        # extract the metadata from the interpreted news
        metadata = interpreted_news.get("metadata", {})
        companies = metadata.get("companies", [])
        regions = metadata.get("regions", [])
        sectors = metadata.get("sectors", [])

        # Extract the summary from the interpreted news
        summary = interpreted_news.get("summary", "No summary available")
        if not summary:
            summary = article_result.summary

        # get the sentiment of the article with news_id for auto-enqueueing
        sentiment = get_sentiment(
            article_result.title + summary,
            use_openai=False,
            use_gemini=True,
            news_id=news_id  # Pass news_id for auto-enqueueing
        )

        keyword = article_result.keywords

        return {
            "text": article_result.text,
            "summary": summary,
            "numerical_score": sentiment["numerical_score"],
            "finbert_score": sentiment["finbert_score"],
            "second_model_score": sentiment["second_model_score"],
            "third_model_score": sentiment["third_model_score"],
            "classification": sentiment["classification"],
            "confidence": sentiment["confidence"],
            "agreement_rate": sentiment["agreement_rate"],
            "keywords": keyword,
            "companies": companies,
            "regions": regions,
            "sectors": sectors,
            "shap": sentiment["shap"],
            "shap_html": sentiment["shap_html"]
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            "text": "An error occurred while fetching the article details",
            "summary": "An error occurred while fetching the article details",
            "numerical_score": 0,
            "finbert_score": 0,
            "second_model_score": 0,
            "third_model_score": 0,
            "classification": "neutral",
            "confidence": 0,
            "agreement_rate": 0,
            "keywords": [],
            "companies": [],
            "regions": [],
            "sectors": [],
        }


def retry_gemini_call(func, *args, max_retries=3, base_delay=2, **kwargs):
    """
    Retry wrapper for Gemini API calls with exponential backoff.

    Handles:
    - 503 Service Unavailable (model overloaded)
    - 429 Too Many Requests (rate limiting)
    - Transient network errors
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e)

            # Check if it's a retriable error
            is_503 = "503" in error_str or "overloaded" in error_str.lower()
            is_429 = "429" in error_str or "rate limit" in error_str.lower()
            is_unavailable = "UNAVAILABLE" in error_str

            if not (is_503 or is_429 or is_unavailable):
                # Non-retriable error, raise immediately
                raise

            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                logging.warning(
                    f"Gemini API error (attempt {attempt + 1}/{max_retries}): {error_str}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                logging.error(f"Gemini API failed after {max_retries} attempts: {error_str}")
                raise


def news_interpreter_summariser(news_text, summary_length):
    """
    Enhanced article summarizer with validation and quality checks.

    Returns:
        str: Summary text, or None if content is invalid
    """
    # Log incoming text for debugging
    text_length = len(news_text) if news_text else 0
    logging.info(f"=" * 80)
    logging.info(f"📝 SUMMARIZER INPUT | Length: {text_length} chars | Target: {summary_length} words")
    logging.info(f"=" * 80)

    if news_text:
        # Show first 300 chars
        preview_start = news_text[:300].replace('\n', ' ').strip()
        logging.info(f"📄 FIRST 300 CHARS: {preview_start}...")

        # Show last 200 chars to see if it's complete
        if text_length > 500:
            preview_end = news_text[-200:].replace('\n', ' ').strip()
            logging.info(f"📄 LAST 200 CHARS: ...{preview_end}")
    else:
        logging.warning("⚠️  EMPTY OR NULL TEXT RECEIVED")

    logging.info(f"=" * 80)

    # Pre-validation: Check if input is valid article content
    if not news_text or len(news_text) < 100:
        logging.warning("Input text too short for summarization")
        return None

    # Check for error page indicators
    ERROR_KEYWORDS = ["javascript", "cookies", "browser not supporting", "reference id",
                      "access denied", "captcha", "verify you are human"]
    text_lower = news_text.lower() if news_text else ""

    if len(news_text) < 300 and any(keyword in text_lower for keyword in ERROR_KEYWORDS):
        logging.warning("⚠️  Input appears to be an error page, skipping summarization")
        return None

    # Use API key for standard Gemini API (no billing required)
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "API key not found. Please set GEMINI_API_KEY in the .env file."
        )

    client = genai.Client(api_key=api_key)

    # Enhanced prompt with clear instructions and constraints
    prompt = f"""You are a professional financial news summarizer. Your task is to create a clear, informative summary of the following news article.

        INSTRUCTIONS:
        1. Write a summary of approximately {summary_length} words (between {int(summary_length * 0.8)} and {int(summary_length * 1.2)} words)
        2. Focus on the KEY FACTS: What happened, who is involved, why it matters, and potential impact
        3. Use COMPLETE SENTENCES - no bullet points, no fragments
        4. Write in THIRD PERSON and maintain a neutral, professional tone
        5. Do NOT include phrases like "The article discusses..." or "According to the text..."
        6. Do NOT summarize meta-information (e.g., "content could not be loaded", "enable JavaScript")
        7. If the article is not about financial news or appears to be an error page, respond with exactly: "INVALID_CONTENT"
        
        ARTICLE TEXT:
        {news_text[:4000]}
        
        SUMMARY:"""

    # Wrap API call with retry logic
    def _make_api_call():
        return client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,  # Lower temperature for more focused summaries
                max_output_tokens=int(summary_length * 5) + 500,
                # Account for model's internal reasoning (thoughts_token_count)
            )
        )

    try:
        response = retry_gemini_call(_make_api_call, max_retries=3, base_delay=3)

        # Simplified logging - only log details if there's an issue
        if response and hasattr(response, 'text') and response.text:
            # Success case - just log that we got a response
            logging.info(f"✓ Gemini response received ({len(response.text)} chars)")
        elif response:
            # Issue case - log detailed debug info
            logging.error(f"🔍 GEMINI RESPONSE DEBUG (text is None):")
            logging.error(f"   - Response type: {type(response)}")

            # Check candidates for issues
            if hasattr(response, 'candidates') and response.candidates:
                for i, candidate in enumerate(response.candidates):
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = str(candidate.finish_reason)
                        logging.error(f"   - Candidate {i} finish_reason: {finish_reason}")

                        # Check for MAX_TOKENS issue
                        if 'MAX_TOKENS' in finish_reason:
                            logging.error(f"     ⚠️  Hit max_output_tokens limit ({int(summary_length * 5) + 500})")

                    if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                        logging.error(f"   - safety_ratings: {candidate.safety_ratings}")

            # Check for prompt_feedback (safety blocks)
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                logging.error(f"   - prompt_feedback: {response.prompt_feedback}")

        # Check if we have a valid response
        if not response:
            logging.error("❌ No response object received from Gemini")
            return None

        if not response.text:
            logging.error("❌ response.text is None - this should not happen after passing validation")
            logging.error("❌ Full response object for debugging:")
            logging.error(f"   - Response repr: {repr(response)}")
            logging.error(
                f"   - Response dict (if available): {response.__dict__ if hasattr(response, '__dict__') else 'N/A'}")
            return None

        # Process the response
        news_summary = response.text.strip()

        # Clean markdown formatting
        news_summary = re.sub(r"```json\s*|\s*```$", "", news_summary)
        news_summary = re.sub(r"```\s*", "", news_summary)
        news_summary = news_summary.strip()

        # Validation checks
        if news_summary == "INVALID_CONTENT":
            logging.warning("Model detected invalid content")
            return None

        if len(news_summary) < 30:
            logging.warning(f"Summary too short ({len(news_summary)} chars): {news_summary[:100]}")
            return None

        # Check if summary contains error indicators
        summary_lower = news_summary.lower()
        if any(keyword in summary_lower for keyword in ["javascript", "cookies", "error loading", "reference id"]):
            logging.warning("Summary contains error keywords, rejecting")
            return None

        # Check for gibberish (less than 70% alphabetic characters)
        alpha_count = sum(1 for c in news_summary if c.isalpha())
        if alpha_count / len(news_summary) < 0.7:
            logging.warning("Summary appears to be gibberish")
            return None

        # Word count validation
        word_count = len(news_summary.split())
        expected_min = int(summary_length * 0.5)  # At least 50% of target

        if word_count < expected_min:
            logging.warning(f"Summary too short: {word_count} words (expected ~{summary_length})")
            return None

        logging.info(f"✓ Generated valid summary: {word_count} words")
        return news_summary

    except Exception as e:
        logging.error(f"Error in summarization: {str(e)}")
        return None


### NEWS_INTERPRETER_TAGGER FUNCTIONS START HERE ###


def extract_info_from_article(article):
    prompt = f"""
    Based on the following article, write very briefly about the companies, regions and sectors involved. Your goal is to clearly and naturally mention:
    Company names involved, using their full security names (e.g. Taiwan Semiconductor Manufacturing Company Limited, not TSM).
    Countries or regions involved, using their full country name (e.g. United States) or World Bank region (i.e. 'South Asia', 'Europe & Central Asia', 'Middle East & North Africa', 'East Asia & Pacific', 'Sub-Saharan Africa', 'Latin America & Caribbean', 'North America').
    Relevant business sectors using their full GICS sector names (i.e. 'Industrials', 'Health Care', 'Information Technology', 'Utilities', 'Financials', 'Materials', 'Consumer Discretionary', 'Real Estate', 'Communication Services', 'Consumer Staples', 'Energy').
    In the event an article does not involve any companies or regions or sectors, then you need not write about that category. Avoid using bullet points or abbreviations. Make sure the summary sounds natural and uses full sentences.
    Here is the article:

    {article}
    """

    try:
        # Use API key for standard Gemini API (no billing required)
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "API key not found. Please set GEMINI_API_KEY in the .env file."
            )

        client = genai.Client(api_key=api_key)

        # Wrap API call with retry logic
        def _make_api_call():
            return client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )

        response_obj = retry_gemini_call(_make_api_call, max_retries=3, base_delay=3)

        if not response_obj or not response_obj.text:
            print("Error: No valid response from Gemini model")
            return None

        raw = response_obj.text
        # print(raw)
        return raw.strip()

    except Exception as e:
        print(f"Error processing article: {e}")
        return None


def combine_company_names(row):
    ner = row.get("company_names_ner")
    llm = row.get("company_names_llm_ner")
    combined = list(
        set(
            x
            for x in (
                    (ner if isinstance(ner, list) else [ner])
                    + (llm if isinstance(llm, list) else [llm])
            )
            if x is not None
        )
    )
    return combined if combined else None


def combine_sectors(row):
    ner = row.get("sectors_ner")
    llm = row.get("sectors_llm_ner")
    combined = list(
        set(
            x
            for x in (
                    (ner if isinstance(ner, list) else [ner])
                    + (llm if isinstance(llm, list) else [llm])
            )
            if x is not None
        )
    )
    return combined if combined else None


def combine_columns_single(val1, val2):
    combined = list(
        set(
            x
            for x in (
                    (val1 if isinstance(val1, list) else [val1])
                    + (val2 if isinstance(val2, list) else [val2])
            )
            if x is not None
        )
    )
    return combined if combined else None


# NOTE: These functions are used by both backend (/resync endpoint) and news-processor
# They require spaCy which is only installed in news-processor, so they will fail in backend
# if called without spaCy being available. The backend should use the news-processor for
# entity extraction instead of calling these directly.

def extract_company(text, confidence_score_arg=90):
    """
    Extract company names from text using spaCy NER and fuzzy matching

    Args:
        text: Text to extract companies from
        confidence_score_arg: Minimum fuzzy match score (0-100)

    Returns:
        List of matched company names or None
    """
    try:
        import spacy
        nlp = spacy.load("en_core_web_trf")
    except ImportError:
        logging.warning("spaCy not available - cannot extract companies")
        return None
    except OSError:
        logging.warning("spaCy model 'en_core_web_trf' not found - cannot extract companies")
        return None

    doc = nlp(str(text))
    orgs = list(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))

    match_list = []
    companies = get_known_companies()  # Lazy load companies list

    for org in orgs:
        match, score, _ = process.extractOne(org, companies)
        if score >= confidence_score_arg:
            match_list.append(match)

    if match_list == []:
        return None
    else:
        unique_list = list(set(match_list))
        return unique_list


def extract_region(text, confidence_score_arg=85):
    """
    Extract regions from text using spaCy NER and fuzzy matching

    Args:
        text: Text to extract regions from
        confidence_score_arg: Minimum fuzzy match score (0-100)

    Returns:
        List of matched regions or None
    """
    try:
        import spacy
        nlp = spacy.load("en_core_web_trf")
    except ImportError:
        logging.warning("spaCy not available - cannot extract regions")
        return None
    except OSError:
        logging.warning("spaCy model 'en_core_web_trf' not found - cannot extract regions")
        return None

    doc = nlp(str(text))
    regions = list(set(ent.text for ent in doc.ents if ent.label_ == "GPE"))

    match_list = []

    for region in regions:
        match, score, _ = process.extractOne(region, country_to_region.keys())
        if score >= confidence_score_arg:
            mapped_region = country_to_region[match]
            match_list.append(mapped_region)

    if not match_list:
        return None
    else:
        return list(set(match_list))  # Return unique mapped regions


def extract_sector(text, threshold=80):
    """
    Extract sectors from text using keyword matching

    Args:
        text: Text to extract sectors from
        threshold: Minimum fuzzy match score (0-100)

    Returns:
        List of matched sectors or None
    """
    return classify_sector(text, threshold)


def classify_sector(text, threshold=80):
    # print("Running classify_sector function")
    text = str(text).lower()
    matched_sectors = []

    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            score = fuzz.partial_ratio(keyword.lower(), text)
            if score >= threshold:
                matched_sectors.append(sector)
                break  # Stop after first match for this sector

    return list(set(matched_sectors)) if matched_sectors else None


def lookup_sectors_from_companies(company_list):
    # print("Running lookup_sectors_from_companies function")
    if not company_list:
        return None
    sp500_plus2 = _get_sp500_dataframe()  # Lazy load dataframe
    sectors = set()
    for company in company_list:
        # print("Current ner company:" + company)
        match = sp500_plus2.loc[sp500_plus2["Security"] == company, "GICS Sector"]
        # print("Current ner sector match:" + match)
        if not match.empty:
            sectors.add(match.iloc[0])
    # print("Returned list of ner sectors:" + ", ".join(list(sectors)))
    return list(sectors) if sectors else None


### NEWS_INTERPRETER_TAGGER FUNCTIONS END HERE ###


def news_interpreter_tagger(news_text, news_summary):
    # Step 1: Extract summary-like LLM response
    # llm_output = extract_info_from_article(news_text)

    # print("Extracting from raw description...")
    company_names_ner = extract_company(news_text, 90)
    regions_ner = extract_region(news_text, 90)

    # print("Extracting from LLM output...")
    company_names_llm_ner = extract_company(news_summary, 90)
    regions_llm_ner = extract_region(news_summary, 90)
    sectors_llm_ner = classify_sector(news_summary, 90)

    # Combine company names
    company_names = combine_company_names(
        {
            "company_names_ner": company_names_ner,
            "company_names_llm_ner": company_names_llm_ner,
        }
    )

    # Sector from company lookup
    sectors_ner = lookup_sectors_from_companies(company_names)

    # Combine sectors
    sectors = combine_sectors(
        {"sectors_ner": sectors_ner, "sectors_llm_ner": sectors_llm_ner}
    )

    # Combine regions
    regions = combine_columns_single(regions_ner, regions_llm_ner)

    # Return result as tuple or dictionary
    return company_names, regions, sectors


def news_interpreter(news_text, summary_length):
    """
    Interpret news article: generate summary and extract entities.

    Returns None if article is invalid to prevent wasted API calls.
    """
    # Early validation: Check if text is valid before ANY API calls
    if not news_text or len(news_text) < 100:
        logging.warning(
            f"⚠️  Article text too short ({len(news_text) if news_text else 0} chars) - skipping ALL processing")
        return None

    # Check for error page indicators
    ERROR_KEYWORDS = ["javascript", "cookies", "browser not supporting", "reference id",
                      "access denied", "captcha", "verify you are human"]
    text_lower = news_text.lower()

    if len(news_text) < 300 and any(keyword in text_lower for keyword in ERROR_KEYWORDS):
        logging.warning("⚠️  Article appears to be error page - skipping ALL processing")
        return None

    # If validation passes, proceed with API calls
    summary = news_interpreter_summariser(news_text, summary_length)

    # If summarization failed, don't bother with entity extraction
    if not summary:
        logging.warning("⚠️  Summary generation failed - skipping entity extraction")
        return None

    companies, regions, sectors = news_interpreter_tagger(news_text, summary)

    return {
        "summary": summary,
        "metadata": {"companies": companies, "regions": regions, "sectors": sectors},
    }


def upload_shap_to_blob(html_content, news_url):
    """
    Upload SHAP HTML explanation to Azure Blob Storage

    Args:
        html_content (str): The HTML content to upload
        news_url (str): The news article URL

    Returns:
        str: The blob URL if successful, None if failed
    """
    try:
        # Get connection string from environment
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            logging.error("Azure Storage connection string not found")
            return None

        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Container name (you can change this)
        container_name = "shap"

        # Generate blob name from URL hash for uniqueness
        import hashlib
        url_hash = hashlib.md5(news_url.encode()).hexdigest()[:12]
        blob_name = f"shap_explanation_{url_hash}.html"

        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        # Upload the HTML content
        blob_client.upload_blob(html_content, overwrite=True, content_type='text/html')

        # Return the blob URL
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        logging.info(f"SHAP HTML uploaded successfully: {blob_url}")
        return blob_url

    except AzureError as e:
        logging.error(f"Azure error uploading SHAP HTML: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error uploading SHAP HTML: {str(e)}")
        return None
