import logging

from flask import jsonify
from newspaper import article
from googlenewsdecoder import new_decoderv1
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re
import pandas as pd
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

sp500_plus2 = pd.DataFrame.from_dict(sp500_plus2_dict)

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

# Create list of known companies
known_companies = sp500_plus2["Security"].tolist()

# Create list of unique GICS sectors
sectors = sp500_plus2["GICS Sector"].unique().tolist()


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

        # Summaries the article text
        interpreted_news = news_interpreter(article_result.text, 100)

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


def news_interpreter_summariser(news_text, summary_length):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "API key not found. Please set the GEMINI_API_KEY in the .env file."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
        Summarize the article in {summary_length} words or less.

        {news_text}
    """

    response = model.generate_content(prompt)

    # Check if we have a valid response
    if (
            not response
            or not response.candidates
            or not response.candidates[0].content.parts
    ):
        print("Error: No valid response received from the model")
        return None

    # Process the response
    news_summary = response.candidates[0].content.parts[0].text

    # Clean the text of any markdown or extra formatting
    clean_text = re.sub(r"```json\s*|\s*```$", "", news_summary)
    clean_text = clean_text.strip()

    # clean_text = "Hello world"
    return clean_text


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
        api_key = os.getenv(
            "GEMINI_API_KEY"
        )  # Replace with env management for security
        if not api_key:
            raise ValueError("API key not found. Please set the GEMINI_API_KEY.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        response_obj = model.generate_content(prompt)

        if (
                not response_obj
                or not response_obj.candidates
                or not response_obj.candidates[0].content.parts
        ):
            print("Error: No valid response from Gemini model")
            return None

        raw = response_obj.candidates[0].content.parts[0].text
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


# DEPRECATED: These functions moved to news-processor microservice
# Extract company using spaCy NER and fuzzy match - now in jobs/news_processing_job.py
#
# def extract_company(text, confidence_score_arg):
#     # print("Next article...")
#     doc = nlp(str(text))
#     orgs = list(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
#     # print("Orgs:" + ", ".join(orgs))
#
#     match_list = []
#
#     for org in orgs:
#         # print("Current org:" + org)
#         match, score, _ = process.extractOne(org, known_companies)
#         # print("Current match:" + match)
#         # print("Current score:" + str(score))
#         if score >= confidence_score_arg:
#             match_list.append(match)
#             # print("Current match list:" + ", ".join(match_list))
#
#     if match_list == []:
#         # print("Returned None")
#         return None
#
#     else:
#         unique_list = list(set(match_list))
#         # print("Final match list:" + ", ".join(unique_list))
#         return unique_list
#
#
# def extract_region(text, confidence_score_arg=85):
#     # cleaned_text = preprocess_text(str(text))
#     # print("cleaned text:" + cleaned_text)
#     doc = nlp(str(text))
#     # print("text:" + text)
#     regions = list(set(ent.text for ent in doc.ents if ent.label_ == "GPE"))
#     # print("regions:"+", ".join(regions))
#
#     match_list = []
#     article = 1
#
#     for region in regions:
#         # print("article" + str(article))
#         article += 1
#         # print("current region:" + region)
#         match, score, _ = process.extractOne(region, country_to_region.keys())
#         # print("match + score:" + match + str(score))
#         if score >= confidence_score_arg:
#             mapped_region = country_to_region[match]
#             match_list.append(mapped_region)
#             # print("current match_list:" + ", ".join(match_list))
#
#     if not match_list:
#         return None
#     else:
#         # print("returned match_list:" + ", ".join(match_list))
#         return list(set(match_list))  # Return unique mapped regions


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


def news_interpreter_tagger(news_text):
    # Step 1: Extract summary-like LLM response
    llm_output = extract_info_from_article(news_text)

    # print("Extracting from raw description...")
    company_names_ner = extract_company(news_text, 90)
    regions_ner = extract_region(news_text, 90)

    # print("Extracting from LLM output...")
    company_names_llm_ner = extract_company(llm_output, 90)
    regions_llm_ner = extract_region(llm_output, 90)
    sectors_llm_ner = classify_sector(llm_output, 90)

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
    summary = news_interpreter_summariser(news_text, summary_length)
    companies, regions, sectors = news_interpreter_tagger(news_text)
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
