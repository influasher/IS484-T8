# NOTE: Heavy ML dependencies (transformers, shap) are now primarily in news-processor
# These are imported lazily only when actually needed to avoid startup overhead
import shap
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re
import logging
import json
import google.generativeai as genai

from app.utils.helpers import upload_shap_to_blob

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
MAX_SEGMENT_LENGTH = 512  # Maximum length for text segments
AGREEMENT_THRESHOLD = 0.7  # 70% agreement required between models
SENTIMENT_THRESHOLD = 0.1  # Threshold for determining positive/negative sentiment

# load environment variables
load_dotenv()


class SentimentAnalyzer:
    def __init__(self):
        self._finbert_pipeline = None  # Lazy loading - don't load model at startup
        self.gemini_client = None
        self.openai_client = None
        logger.info("Sentiment Analyzer initialized (FinBERT model will be loaded on first use)")

    @property
    def finbert_pipeline(self):
        """Lazy load FinBERT model on first access"""
        if self._finbert_pipeline is None:
            logger.info("Loading FinBERT model on first use...")
            self._finbert_pipeline = self._load_finbert()
            logger.info("FinBERT model loaded successfully")
        return self._finbert_pipeline

    def _load_finbert(self):
        """Initialize and load the FinBERT model"""
        # Lazy import transformers only when actually loading the model
        try:
            from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as e:
            logger.error("transformers library not installed - this is expected in lightweight backend")
            raise ImportError(
                "transformers is not installed. "
                "This functionality is only available in the news-processor microservice."
            ) from e

        model_name = "yiyanghkust/finbert-tone"
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            return pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        except Exception as e:
            logger.error(f"Error loading FinBERT model: {e}")
            raise

    def _load_gemini(self):
        """Initialize Gemini AI client"""
        try:
            # Direct API key for testing purposes
            load_dotenv()

            # Try GEMINI_API_KEY_SW first (secondary key), fallback to GEMINI_API_KEY
            api_key = os.getenv("GEMINI_API_KEY_SW") or os.getenv("GEMINI_API_KEY")

            # Configure the Gemini API client
            genai.configure(api_key=api_key)
            self.gemini_client = genai.GenerativeModel("gemini-2.0-flash")

            logger.info("Gemini AI client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading Gemini client: {e}")
            raise

    def _load_openai(self):
        """Initialize OpenAI client"""
        try:
            # Direct API key for testing purposes
            load_dotenv()

            self.openai_api_key = os.getenv(
                "OPENAI_API_KEY"
            )  # REPLACE WITH YOUR ACTUAL API KEY

            # We're not using the client library directly anymore, just storing the API key
            logger.info("OpenAI API key stored successfully")
            return True
        except Exception as e:
            logger.error(f"Error storing OpenAI API key: {e}")
            raise

    def preprocess_text(self, text):
        """
        Preprocess the input text for sentiment analysis
        - Entity extraction
        - Text summarization
        """
        # Remove URLs
        text = re.sub(r"http\S+", "", text)

        # Remove special characters but keep punctuation important for sentiment
        text = re.sub(r'[^\w\s.,!?:;\'"-]', "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        logger.debug(f"Preprocessed text: {text[:100]}...")
        return text

    def split_text(self, text):
        """
        Split the text into segments for processing
        - Handle character limits
        - Preserve context between segments
        """
        if len(text) <= MAX_SEGMENT_LENGTH:
            return [text]

        # Split by sentences to preserve context
        sentences = re.split(r"(?<=[.!?])\s+", text)
        segments = []
        current_segment = ""

        for sentence in sentences:
            if len(current_segment) + len(sentence) <= MAX_SEGMENT_LENGTH:
                current_segment += " " + sentence if current_segment else sentence
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence

        if current_segment:
            segments.append(current_segment.strip())

        logger.info(f"Split text into {len(segments)} segments")
        return segments

    def analyze_with_finbert(self, text):
        """
        Analyze sentiment using FinBERT model
        Returns a dictionary with sentiment scores
        """
        try:
            results = self.finbert_pipeline(text)

            # Extract scores and convert to proper format
            scores_dict = {item["label"].lower(): item["score"] for item in results}

            # Calculate numerical score (-1.0 to +1.0)
            numerical_score = scores_dict.get("positive", 0) - scores_dict.get(
                "negative", 0
            )

            classification = (
                "positive"
                if numerical_score > SENTIMENT_THRESHOLD
                else "negative" if numerical_score < -SENTIMENT_THRESHOLD else "neutral"
            )

            return {
                "numerical_score": numerical_score,
                "classification": classification,
                "detailed_scores": scores_dict,
            }
        except Exception as e:
            logger.error(f"Error analyzing with FinBERT: {e}")
            return {
                "numerical_score": 0,
                "classification": "neutral",
                "detailed_scores": {},
            }

    def analyze_with_gemini(self, text):
        """
        Analyze sentiment using Gemini AI
        Returns a dictionary with sentiment scores
        """
        try:
            # Ensure Gemini client is initialized
            if not self.gemini_client:
                self._load_gemini()

            # Create prompt for sentiment analysis
            prompt = f"""
            Analyze the sentiment of the following financial news text. 
            Rate the sentiment on a scale from 0.0 to 1.0, where:
            - 0.0 is extremely negative/bearish
            - 0.5 is neutral
            - 1.0 is extremely positive/bullish
            
            Respond with a JSON object containing:
            - positive_score: a float value between 0 and 1
            - negative_score: a float value between 0 and 1
            - neutral_score: a float value between 0 and 1
            - overall_score: a float value between 0 and 1 (where 0.5 is neutral)
            - classification: one of "positive", "negative", or "neutral"
            
            Text to analyze: {text}
            """

            # Call Gemini API
            response = self.gemini_client.generate_content(prompt)
            response_text = response.text

            logger.info(response_text)

            # Parse the response - handling the possibility that it might not be valid JSON
            try:
                # Extract JSON from response if it's enclosed in code blocks
                if "```json" in response_text:
                    json_content = (
                        response_text.split("```json")[1].split("```")[0].strip()
                    )
                    result = json.loads(json_content)
                elif "```" in response_text:
                    json_content = response_text.split("```")[1].split("```")[0].strip()
                    result = json.loads(json_content)
                else:
                    result = json.loads(response_text)

                # Ensure we have the expected keys
                positive_score = result.get("positive_score", 0.0)
                negative_score = result.get("negative_score", 0.0)
                neutral_score = result.get("neutral_score", 0.0)
                overall_score = result.get("overall_score", 0.5)
                classification = result.get("classification", "neutral")

                # Convert overall_score to numerical_score (-1.0 to 1.0 scale)
                numerical_score = (overall_score - 0.5) * 2

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    f"Could not parse Gemini response as JSON: {e}. Using fallback parsing."
                )

                # Fallback parsing - extract scores using regex
                positive_match = re.search(
                    r'positive_score["\s:]+([0-9.]+)', response_text
                )
                positive_score = (
                    float(positive_match.group(1)) if positive_match else 0.0
                )

                negative_match = re.search(
                    r'negative_score["\s:]+([0-9.]+)', response_text
                )
                negative_score = (
                    float(negative_match.group(1)) if negative_match else 0.0
                )

                # Add missing neutral_score extraction
                neutral_match = re.search(
                    r'neutral_score["\s:]+([0-9.]+)', response_text
                )
                neutral_score = (
                    float(neutral_match.group(1)) if neutral_match else 0.0
                )

                overall_match = re.search(
                    r'overall_score["\s:]+([0-9.]+)', response_text
                )
                overall_score = float(overall_match.group(1)) if overall_match else 0.5

                # Calculate numerical_score (-1.0 to 1.0 scale)
                numerical_score = (overall_score - 0.5) * 2

                # Determine classification
                if "positive" in response_text.lower():
                    classification = "positive"
                elif "negative" in response_text.lower():
                    classification = "negative"
                else:
                    classification = "neutral"

            return {
                "numerical_score": numerical_score,
                "classification": classification,
                "detailed_scores": {
                    "positive": positive_score,
                    "negative": negative_score,
                    "neutral": neutral_score,
                    "overall": overall_score,
                },
            }
        except Exception as e:
            logger.error(f"Error analyzing with Gemini: {e}")
            return {
                "numerical_score": 0,
                "classification": "neutral",
                "detailed_scores": {},
            }

    def analyze_with_openai(self, text):
        """
        Analyze sentiment using OpenAI API directly
        Returns a dictionary with sentiment scores
        """
        try:
            # Ensure OpenAI API key is initialized
            if not hasattr(self, "openai_api_key"):
                self._load_openai()

            # API endpoint for OpenAI
            API_URL = "https://api.openai.com/v1/chat/completions"

            # Create prompt for sentiment analysis
            system_prompt = """
            You are a financial sentiment analysis system. Analyze the sentiment of financial news text.
            Rate the sentiment on a scale from 0.0 to 1.0, where:
            - 0.0 is extremely negative/bearish
            - 0.5 is neutral
            - 1.0 is extremely positive/bullish
            
            Respond with ONLY a JSON object containing:
            - positive_score: a float value between 0 and 1
            - negative_score: a float value between 0 and 1
            - neutral_score: a float value between 0 and 1
            - overall_score: a float value between 0 and 1 (where 0.5 is neutral)
            - classification: one of "positive", "negative", or "neutral"
            """

            user_prompt = f"Text to analyze: {text}"

            # Prepare request
            import requests

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}",
            }

            body = {
                "model": "gpt-4o-mini",  # Updated model name (gpt-4-turbo-preview deprecated)
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 150,
                "temperature": 0.3,  # Low temperature for more consistent results
            }

            # Call OpenAI API
            response = requests.post(API_URL, headers=headers, json=body)

            # Check for successful response
            if response.status_code != 200:
                logger.error(
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )
                raise Exception(
                    f"OpenAI API returned status code {response.status_code}"
                )

            # Parse the response
            response_data = response.json()
            result_text = response_data["choices"][0]["message"]["content"]
            result = json.loads(result_text)

            # Extract the values
            positive_score = result.get("positive_score", 0.0)
            negative_score = result.get("negative_score", 0.0)
            neutral_score = result.get("neutral_score", 0.0)
            overall_score = result.get("overall_score", 0.5)
            classification = result.get("classification", "neutral")

            # Convert overall_score to numerical_score (-1.0 to 1.0 scale)
            numerical_score = (overall_score - 0.5) * 2

            return {
                "numerical_score": numerical_score,
                "classification": classification,
                "detailed_scores": {
                    "positive": positive_score,
                    "negative": negative_score,
                    "neutral": neutral_score,
                    "overall": overall_score,
                },
            }
        except Exception as e:
            logger.error(f"Error analyzing with OpenAI: {e}")
            return {
                "numerical_score": 0,
                "classification": "neutral",
                "detailed_scores": {},
            }

    def weighted_integration(self, finbert_result, second_model_result):
        """
        Implement the Weighted Integration Algorithm (WIP)
        - Model consensus evaluation (70% agreement required)
        - Confidence score calculation based on model agreement
        - Normalization to scale of -100 (bearish) to +100 (bullish)
        """
        # Check model agreement
        models_agree = (
                finbert_result["classification"] == second_model_result["classification"]
        )

        # Calculate base score (average of the two models)
        # FinBERT range: -1.0 to +1.0, Second model range is similar for our purposes
        base_score = (
                             finbert_result["numerical_score"] + second_model_result["numerical_score"]
                     ) / 2

        # Calculate confidence score based on model agreement and score differences
        score_difference = abs(
            finbert_result["numerical_score"] - second_model_result["numerical_score"]
        )
        confidence = 1.0 if models_agree else max(0.0, 1.0 - score_difference)

        # Apply confidence to score
        adjusted_score = base_score * confidence

        # Normalize to -100 to +100 scale
        normalized_score = adjusted_score * 100

        # Final classification with financial terminology
        if normalized_score > 10:
            classification = "bullish"
        elif normalized_score < -10:
            classification = "bearish"
        else:
            classification = "neutral"

        return {
            "numerical_score": normalized_score,
            "classification": classification,
            "models_agree": models_agree,
            "confidence": confidence,
            "model_scores": {
                "finbert": finbert_result["numerical_score"],
                "second_model": second_model_result["numerical_score"],
            },
        }

    def analyze_sentiment(self, text, use_openai=True):
        """
        Main function to analyze sentiment of financial text
        - Preprocessing
        - Text splitting
        - Model processing
        - Score integration

        Parameters:
        - text: The text to analyze
        - use_openai: Whether to use OpenAI as the second model (if False, uses Gemini)

        Returns a dictionary with integrated sentiment analysis
        """
        # Preprocess the text
        preprocessed_text = self.preprocess_text(text)

        # Split the text into manageable segments
        text_segments = self.split_text(preprocessed_text)

        # Process each segment with both models (with graceful error handling)
        finbert_results = []
        second_model_results = []

        for segment in text_segments:
            # FinBERT analysis (always try this first)
            try:
                finbert_result = self.analyze_with_finbert(segment)
                finbert_results.append(finbert_result)
            except Exception as e:
                logger.error(f"FinBERT analysis failed: {str(e)}")
                finbert_results.append({
                    "numerical_score": 0,
                    "classification": "neutral",
                    "detailed_scores": {}
                })

            # Second model analysis (OpenAI or Gemini)
            try:
                if use_openai:
                    second_result = self.analyze_with_openai(segment)
                else:
                    second_result = self.analyze_with_gemini(segment)
                second_model_results.append(second_result)
            except Exception as e:
                model_name = "OpenAI" if use_openai else "Gemini"
                logger.error(f"{model_name} analysis failed: {str(e)}")
                second_model_results.append({
                    "numerical_score": 0,
                    "classification": "neutral",
                    "detailed_scores": {}
                })

        # Integrate scores for each segment
        integrated_results = []
        for i in range(len(text_segments)):
            integrated_results.append(
                self.weighted_integration(finbert_results[i], second_model_results[i])
            )

        # Aggregate results from all segments
        if not integrated_results:
            return {
                "numerical_score": 0,
                "classification": "neutral",
                "confidence": 0,
                "segment_count": 0,
            }

        # Calculate weighted average based on confidence
        total_weight = sum(result["confidence"] for result in integrated_results)
        if total_weight == 0:
            total_weight = 1  # Avoid division by zero

        print(integrated_results)

        # Calculate final scores
        final_score = (
                sum(
                    result["numerical_score"] * result["confidence"]
                    for result in integrated_results
                )
                / total_weight
        )
        final_finbert_score = (
                                      sum(
                                          result["model_scores"]["finbert"] * result["confidence"]
                                          for result in integrated_results
                                      )
                                      / total_weight
                              ) * 100
        final_second_model_score = (
                                           sum(
                                               result["model_scores"]["second_model"] * result["confidence"]
                                               for result in integrated_results
                                           )
                                           / total_weight
                                   ) * 100

        # Final classification
        if final_score > 10:
            final_classification = "bullish"
        elif final_score < -10:
            final_classification = "bearish"
        else:
            final_classification = "neutral"

        # Calculate average confidence
        avg_confidence = sum(
            result["confidence"] for result in integrated_results
        ) / len(integrated_results)

        # Calculate agreement rate
        agreement_count = sum(
            1 for result in integrated_results if result["models_agree"]
        )
        agreement_rate = agreement_count / len(integrated_results)

        # Calculate shap values for FinBert scores (with error handling)
        shap_json = None
        shap_html = None
        try:
            shap_explanation = self.get_shap_explanation(preprocessed_text)
            shap_json = self.shap_explanation_to_json(shap_explanation)
            shap_html = self.generate_shap_html(shap_explanation)
        except Exception as e:
            logger.warning(f"SHAP generation failed (non-critical): {str(e)}")
            # Continue without SHAP - it's not critical for sentiment analysis

        return {
            "numerical_score": final_score,
            "finbert_score": final_finbert_score,
            "second_model_score": final_second_model_score,
            "classification": final_classification,
            "confidence": avg_confidence,
            "agreement_rate": agreement_rate,
            "segment_count": len(text_segments),
            "segment_results": integrated_results,
            "shap": shap_json,
            "shap_html": shap_html

        }

    def get_shap_explanation(self, text: str):
        """
        Get SHAP explanation for the sentiment analysis of the text using FinBERT model
        """
        # Lazy import shap only when actually needed
        try:
            import shap
        except ImportError as e:
            logger.error("shap library not installed - this is expected in lightweight backend")
            raise ImportError(
                "shap is not installed. "
                "This functionality is only available in the news-processor microservice."
            ) from e

        explainer = shap.Explainer(self.finbert_pipeline)
        explanation = explainer([text])
        return explanation

    def shap_explanation_to_json(self, explanation):
        """
        Convert SHAP explanation to JSON serializable format
        """
        tokens = explanation.data[0].tolist()
        shap_values = explanation.values[0].tolist()
        base_values = explanation.base_values[0].tolist()

        result = {
            "tokens": tokens,
            "shap_values": shap_values,
            "base_values": base_values
        }
        return json.dumps(result)

    # def generate_shap_html(self, explanation) -> str:
    #     """
    #     Generate HTML representation of SHAP explanation
    #     """
    #     # Lazy import shap only when actually needed
    #     try:
    #         import shap
    #     except ImportError as e:
    #         logger.error("shap library not installed - this is expected in lightweight backend")
    #         raise ImportError(
    #             "shap is not installed. "
    #             "This functionality is only available in the news-processor microservice."
    #         ) from e
    #
    #     html = shap.plots.text(explanation[0], display=False)
    #     return html

    def generate_shap_html(self, explanation) -> str:
        """
        Generate improved HTML representation of SHAP explanation with better styling
        """
        # Lazy import shap only when actually needed
        try:
            import shap
        except ImportError as e:
            logger.error("shap library not installed - this is expected in lightweight backend")
            raise ImportError(
                "shap is not installed. "
                "This functionality is only available in the news-processor microservice."
            ) from e

        text_plot = shap.plots.text(explanation, display=False)
        basic_html = f"<head>{shap.getjs()}</head><body>{text_plot}</body>"

        basic_html = self.keep_red_highlighted_tab(basic_html)

        # Enhanced HTML with improved CSS to prevent overlaps
        enhanced_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SHAP Sentiment Analysis Explanation</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                    background-color: #f8f9fa;
                    color: #333;
                }}
                .shap-container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .shap-title {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    color: #2c3e50;
                    text-align: center;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                .shap-visualization {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #fafafa;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                    overflow-x: auto;
                    overflow-y: visible;
                }}

                /* Fix SHAP text plot overlaps */
                .shap-visualization span {{
                    display: inline-block !important;
                    margin: 2px 1px !important;
                    padding: 2px 4px !important;
                    white-space: nowrap !important;
                    line-height: 1.8 !important;
                }}

                .shap-visualization .negative {{
                    background-color: rgba(0, 136, 255, 0.3) !important;
                    border-radius: 3px;
                }}

                .shap-visualization .positive {{
                    background-color: rgba(255, 13, 87, 0.3) !important;
                    border-radius: 3px;
                }}

                /* Ensure text wraps properly */
                .shap-visualization div {{
                    word-wrap: break-word !important;
                    overflow-wrap: break-word !important;
                    line-height: 2 !important;
                }}

                .shap-legend {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f1f3f4;
                    border-radius: 5px;
                    font-size: 14px;
                }}
                .shap-legend-item {{
                    display: block;
                    margin-bottom: 10px;
                }}
                .color-box {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    margin-right: 10px;
                    border-radius: 3px;
                    vertical-align: middle;
                }}
                .positive-box {{
                    background: rgba(255, 13, 87, 0.5);
                }}
                .negative-box {{
                    background: rgba(0, 136, 255, 0.5);
                }}
                .info-section {{
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #e8f4f8;
                    border-left: 4px solid #3498db;
                    border-radius: 5px;
                }}
                .info-title {{
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 10px;
                    font-size: 18px;
                }}
                @media (max-width: 768px) {{
                    body {{
                        margin: 10px;
                    }}
                    .shap-container {{
                        padding: 15px;
                    }}
                    .shap-title {{
                        font-size: 20px;
                    }}
                    .shap-visualization {{
                        padding: 10px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="shap-container">
                <div class="shap-title">
                    SHAP Explanation: Word Contributions to Sentiment
                </div>

                <div class="shap-legend">
                    <div class="info-title">How to interpret:</div>
                    <div class="shap-legend-item">
                        <span class="color-box positive-box"></span>
                        <strong>Red highlights</strong> = words that push toward the displayed sentiment category
                    </div>
                    <div class="shap-legend-item">
                        <span class="color-box negative-box"></span>
                        <strong>Blue highlights</strong> = words that push away from the displayed sentiment category
                    </div>
                    <div style="margin-top: 10px;">
                        <strong>Intensity:</strong> Darker colors = stronger influence
                    </div>
                </div>

                <div class="shap-visualization">
                    {basic_html}
                </div>

                <div class="info-section">
                    <div class="info-title">About SHAP Values</div>
                    <p><strong>SHAP (SHapley Additive exPlanations)</strong> measures each word's contribution to the model's prediction.</p>
                    <p><strong>Red words</strong> increase confidence in the displayed sentiment class, while <strong>blue words</strong> decrease it.</p>
                    <p>This helps you understand <em>why</em> the model classified the text as positive, negative, or neutral based on specific words and phrases.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return enhanced_html

    def keep_red_highlighted_tab(self, html: str) -> str:
        RED_BG = "rgba(255.0, 13.0, 87.0, 1.0)"  # the highlight color in your HTML

        soup = BeautifulSoup(html, "html.parser")

        # tabs look like: <div id="..._output_1_name" ...>Positive</div>
        tab_headers = soup.find_all("div", id=lambda x: x and "_output_" in x and x.endswith("_name"))

        if not tab_headers:
            return html

        # 1. find the tab with the red background
        active_tab = None
        for tab in tab_headers:
            style = tab.get("style", "")
            # make it a bit tolerant to spaces
            if "background:" in style and RED_BG in style:
                active_tab = tab
                break

        # fallback: if none has the red background, just keep the first one
        if active_tab is None:
            active_tab = tab_headers[0]

        active_id = active_tab.get("id")
        content_id = active_id[:-5]  # strip "_name" → ..._output_1

        # 2. remove other tabs
        for tab in tab_headers:
            if tab is not active_tab:
                tab.decompose()

        # 3. keep only the matching panel
        panels = soup.find_all("div", id=lambda x: x and "_output_" in x and not x.endswith("_name"))
        for panel in panels:
            if panel.get("id") != content_id:
                panel.decompose()
            else:
                # ensure visible
                style = panel.get("style", "")
                if "display: block" not in style:
                    style = (style + ";display: block").lstrip(";")
                    panel["style"] = style

        return str(soup)


# Expose a simple interface for external use
def get_sentiment(text, use_openai=True, use_gemini=False):
    """
    Analyze the sentiment of a financial text using the SentimentAnalyzer
    with graceful degradation if models fail.

    Parameters:
    - text: The text to analyze
    - use_openai: Whether to use OpenAI as the second model (if False, uses Gemini)
    - use_gemini: Whether to use Gemini as the second model (if False, uses OpenAI)

    Returns a dictionary with sentiment analysis results.
    Will use at least 2 models if available, degrading gracefully if models fail.
    """
    analyzer = SentimentAnalyzer()

    if use_openai and use_gemini:
        # Analyze with both models
        result_with_open_ai = analyzer.analyze_sentiment(text, use_openai=True)
        result_with_gemini = analyzer.analyze_sentiment(text, use_openai=False)

        result = {
            "numerical_score": 0,
            "classification": "neutral",
            "finbert_score": 0,
            "second_model_score": 0,
            "third_model_score": 0,
            "confidence": 0,
            "agreement_rate": 0,
            "shap": {},
            "shap_html": ""
        }

        # Combine results
        result["numerical_score"] = (
                                            result_with_open_ai["numerical_score"]
                                            + result_with_gemini["numerical_score"]
                                    ) / 2
        result["finbert_score"] = (
                                          result_with_open_ai["finbert_score"] + result_with_gemini["finbert_score"]
                                  ) / 2
        result["second_model_score"] = result_with_gemini["second_model_score"]
        result["third_model_score"] = result_with_open_ai["numerical_score"]
        result["confidence"] = (
                                       result_with_open_ai["confidence"] + result_with_gemini["confidence"]
                               ) / 2
        result["agreement_rate"] = (
                                           result_with_open_ai["agreement_rate"] + result_with_gemini["agreement_rate"]
                                   ) / 2

        # get calculated classification
        if result["numerical_score"] > 10:
            result["classification"] = "bullish"
        elif result["numerical_score"] < -10:
            result["classification"] = "bearish"
        else:
            result["classification"] = "neutral"

        # get shap values
        result["shap"] = result_with_open_ai["shap"]

        # get shap url
        result["shap_html"] = result_with_open_ai["shap_html"]

        return {
            "numerical_score": result["numerical_score"],
            "finbert_score": result["finbert_score"],
            "second_model_score": result["second_model_score"],
            "third_model_score": result["third_model_score"],
            "classification": result["classification"],
            "confidence": result["confidence"],
            "agreement_rate": result["agreement_rate"],
            "shap": result["shap"],
            "shap_html": result["shap_html"]
        }

    elif use_gemini:
        # Analyze with Gemini only
        result = analyzer.analyze_sentiment(text, use_openai=False)

        # Return a simplified result object for external use
        return {
            "numerical_score": result["numerical_score"],
            "finbert_score": result["finbert_score"],
            "second_model_score": result["second_model_score"],
            "third_model_score": 0,
            "classification": result["classification"],
            "confidence": result["confidence"],
            "agreement_rate": result["agreement_rate"],
            "shap": result["shap"],
            "shap_html": result["shap_html"]
        }


# Example usage
# Testing code for SHAP HTML generation
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    sample_text = """
The Wall Street Journal article discusses the potential of quantum computing to revolutionize industries, but cautions investors about the risks and uncertainties involved. While quantum technology is advancing rapidly, it's still in its early stages and widespread adoption is years away. Current quantum computing companies face challenges in proving their value and achieving profitability. The article suggests a long-term investment horizon and careful evaluation of companies, emphasizing the need for investors to focus on established tech companies with quantum initiatives rather than pure-play quantum startups.

    """

    print("=== Testing SHAP HTML Generation ===")

    try:
        # Get SHAP explanation
        print("1. Getting SHAP explanation...")
        explanation = analyzer.get_shap_explanation(sample_text)
        print("   ✓ SHAP explanation generated successfully")

        # Convert to JSON
        print("2. Converting SHAP explanation to JSON...")
        shap_json = analyzer.shap_explanation_to_json(explanation)
        print("   ✓ JSON conversion successful")
        print(f"   JSON preview: {shap_json[:200]}...")

        # Generate HTML
        print("3. Generating enhanced SHAP HTML...")
        shap_html = analyzer.generate_shap_html(explanation)
        print("   ✓ HTML generation successful")

        # Save HTML to file for viewing
        output_file = "shap_sentiment_explanation.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(shap_html)
        print(f"   ✓ HTML saved to {output_file}")

        # Print some basic info about the explanation
        print("\n=== SHAP Analysis Summary ===")
        print(f"Number of tokens: {len(explanation.data[0])}")
        print(f"Base values shape: {explanation.base_values[0].shape}")
        print(f"SHAP values shape: {explanation.values[0].shape}")

        # Show first few tokens with their SHAP values
        tokens = explanation.data[0]
        values = explanation.values[0]
        print("\nFirst 10 tokens with SHAP values:")
        for i in range(min(10, len(tokens))):
            print(f"  '{tokens[i]}': {values[i]}")

        print(f"\n✓ Complete! Open {output_file} in your browser to view the visualization.")

    except ImportError as e:
        print(f"❌ Import error (expected in lightweight backend): {e}")
    except Exception as e:
        print(f"❌ Error during SHAP testing: {e}")
        import traceback

        traceback.print_exc()

    # Test basic FinBERT functionality (should work even without SHAP)
    print("\n=== Testing Basic FinBERT Analysis ===")
    try:
        finbert_result = analyzer.analyze_with_finbert(sample_text)
        print(f"✓ FinBERT Sentiment: {finbert_result['classification']}")
        print(f"✓ FinBERT Score: {finbert_result['numerical_score']:.2f}")
        print(f"✓ FinBERT Details: {finbert_result['detailed_scores']}")
    except Exception as e:
        print(f"❌ FinBERT analysis failed: {e}")

    # Test comparison between FinBERT and both models
    # try:
    #     finbert_result = analyzer.analyze_with_finbert(sample_text)
    #
    #     # Set your API keys here for quick testing
    #     # analyzer.gemini_client = None  # Reset to force initialization
    #     # analyzer._load_gemini()
    #     # gemini_result = analyzer.analyze_with_gemini(sample_text)
    #
    #     # shap.Explainer()
    #
    #     print("\n=== Model Comparison ===")
    #     print(f"FinBERT Classification: {finbert_result['classification']}")
    #     print(f"FinBERT Score: {finbert_result['numerical_score']:.2f}")
    #     # print(f"Gemini Classification: {gemini_result['classification']}")
    #     # print(f"Gemini Score: {gemini_result['numerical_score']:.2f}")
    #
    #     # Uncomment to also test OpenAI (replace YOUR_OPENAI_API_KEY_HERE with your actual key)
    #
    #     # openai_result = analyzer.analyze_with_openai(sample_text)
    #     # print(f"OpenAI Classification: {openai_result['classification']}")
    #     # print(f"OpenAI Score: {openai_result['numerical_score']:.2f}")
    #
    #     # Integrated results
    #     # integrated = analyzer.weighted_integration(finbert_result, gemini_result)
    #     # print("\n=== Integrated Result ===")
    #     # print(f"Classification: {integrated['classification']}")
    #     # print(f"Score: {integrated['numerical_score']:.2f}")
    #     # print(f"Models agree: {integrated['models_agree']}")
    #     # print(f"Confidence: {integrated['confidence']:.2f}")
    #
    # except Exception as e:
    #     print(f"Error during comparison test: {e}")
