from dotenv import load_dotenv
import os
import re
import logging
import json
import google.generativeai as genai
import numpy as np
from app.services.sentiment.active_learning import should_request_human_feedback, identify_disagreement_samples, ActiveLearningSelector

from app.utils.helpers import upload_shap_to_blob
from app.services.sentiment.features import SentimentFeatureBuilder

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
        self.feature_builder = SentimentFeatureBuilder()

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
        Analyze sentiment using FinBERT model with improved error handling
        """
        try:
            results = self.finbert_pipeline(text)
            
            # Validate results structure
            if not results or not isinstance(results, list):
                return self._get_default_sentiment_result()
            
            # Extract scores and validate
            scores_dict = {}
            for item in results:
                if isinstance(item, dict) and 'label' in item and 'score' in item:
                    label = item['label'].lower()
                    score = item['score']
                    # Validate score is a valid number
                    if isinstance(score, (int, float)) and not np.isnan(score) and not np.isinf(score):
                        scores_dict[label] = float(score)
            
            # Ensure we have the required labels with valid defaults
            positive_score = scores_dict.get('positive', 0.33)
            negative_score = scores_dict.get('negative', 0.33)
            neutral_score = scores_dict.get('neutral', 0.34) 
            
            # Normalize scores to ensure they sum to 1.0 and are valid
            total = positive_score + negative_score + neutral_score
            if total <= 0 or np.isnan(total) or np.isinf(total):
                # Fallback to uniform distribution
                positive_score = negative_score = neutral_score = 1/3
                total = 1.0
            else:
                positive_score /= total
                negative_score /= total
                neutral_score /= total
            
            # Calculate numerical score with validation
            numerical_score = positive_score - negative_score
            if np.isnan(numerical_score) or np.isinf(numerical_score):
                numerical_score = 0.0
            
            # Determine classification
            if numerical_score > SENTIMENT_THRESHOLD:
                classification = "positive"
            elif numerical_score < -SENTIMENT_THRESHOLD:
                classification = "negative"
            else:
                classification = "neutral"
            
            return {
                "numerical_score": numerical_score,
                "classification": classification,
                "detailed_scores": {
                    'positive': positive_score,
                    'negative': negative_score,
                    'neutral': neutral_score
                },
            }
            
        except Exception as e:
            logger.error(f"Error analyzing with FinBERT: {e}")
            return self._get_default_sentiment_result()
    
    def _get_default_sentiment_result(self):
        """Return a safe default sentiment result when models fail"""
        return {
            "numerical_score": 0.0,
            "classification": "neutral",
            "detailed_scores": {
                'positive': 0.33,
                'negative': 0.33,
                'neutral': 0.34
            },
        }

    def analyze_with_gemini(self, text):
        """
        Analyze sentiment using Gemini AI with improved validation
        """
        try:
            if not self.gemini_client:
                self._load_gemini()

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

            response = self.gemini_client.generate_content(prompt)
            response_text = response.text

            # Parse and validate response
            positive_score, negative_score, neutral_score, overall_score, classification = self._parse_llm_response(
                response_text, "gemini"
            )
            
            # Calculate numerical score with validation
            numerical_score = (overall_score - 0.5) * 2
            if np.isnan(numerical_score) or np.isinf(numerical_score):
                numerical_score = 0.0

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
            return self._get_default_sentiment_result()

    def analyze_with_openai(self, text):
        """
        Analyze sentiment using OpenAI API with improved validation
        """
        try:
            if not hasattr(self, "openai_api_key"):
                self._load_openai()

            # API endpoint for OpenAI
            API_URL = "https://api.openai.com/v1/chat/completions"
            
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
            import requests

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}",
            }

            body = {
                "model": "gpt-4-turbo-preview",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 150,
                "temperature": 0.3,
            }

            response = requests.post(API_URL, headers=headers, json=body)

            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return self._get_default_sentiment_result()

            response_data = response.json()
            result_text = response_data["choices"][0]["message"]["content"]
            
            # Parse and validate response  
            positive_score, negative_score, neutral_score, overall_score, classification = self._parse_llm_response(
                result_text, "openai"
            )
            
            # Calculate numerical score with validation
            numerical_score = (overall_score - 0.5) * 2
            if np.isnan(numerical_score) or np.isinf(numerical_score):
                numerical_score = 0.0

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
            return self._get_default_sentiment_result()
    
    def _parse_llm_response(self, response_text: str, model_name: str):
        """
        Parse and validate LLM response with robust fallbacks
        Returns: (positive_score, negative_score, neutral_score, overall_score, classification)
        """
        try:
            # Try JSON parsing first
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_content)
            elif "```" in response_text:
                json_content = response_text.split("```")[1].split("```")[0].strip()
                result = json.loads(json_content)
            else:
                result = json.loads(response_text)

            # Extract and validate scores
            positive_score = self._validate_score(result.get("positive_score", 0.33))
            negative_score = self._validate_score(result.get("negative_score", 0.33))
            neutral_score = self._validate_score(result.get("neutral_score", 0.34))
            overall_score = self._validate_score(result.get("overall_score", 0.5), min_val=0.0, max_val=1.0)
            classification = result.get("classification", "neutral")
            
        except (json.JSONDecodeError, KeyError) as e:
            
            # Regex fallback with validation
            positive_score = self._extract_score_regex(response_text, 'positive_score', 0.33)
            negative_score = self._extract_score_regex(response_text, 'negative_score', 0.33) 
            neutral_score = self._extract_score_regex(response_text, 'neutral_score', 0.34)
            overall_score = self._extract_score_regex(response_text, 'overall_score', 0.5)
            
            # Determine classification from text
            if "positive" in response_text.lower():
                classification = "positive"
            elif "negative" in response_text.lower():
                classification = "negative"
            else:
                classification = "neutral"
        
        # Normalize probability scores
        total = positive_score + negative_score + neutral_score
        if total <= 0:
            positive_score = negative_score = neutral_score = 1/3
        else:
            positive_score /= total
            negative_score /= total  
            neutral_score /= total
            
        return positive_score, negative_score, neutral_score, overall_score, classification
    
    def _validate_score(self, value, min_val=0.0, max_val=1.0, default=0.33):
        """Validate and clamp score values"""
        try:
            score = float(value)
            if np.isnan(score) or np.isinf(score):
                return default
            return max(min_val, min(max_val, score))
        except (TypeError, ValueError):
            return default
    
    def _extract_score_regex(self, text: str, score_name: str, default: float):
        """Extract score using regex with validation"""
        try:
            match = re.search(rf'{score_name}["\s:]+([0-9.]+)', text)
            if match:
                return self._validate_score(match.group(1), default=default)
            return default
        except Exception:
            return default

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

    def enhanced_weighted_integration(self, finbert_result, second_model_result, 
                                    text, model_type='gemini'):
        """
        Enhanced integration using feature-based weighting
        """
        # Build features for this sample
        features, feature_names = self.feature_builder.build_single_sample_features(
            finbert_result, second_model_result, text, model_type
        )
        
        # For now, use rule-based weighting based on features
        # This will be replaced by trained meta-classifier later
        finbert_weight = self._calculate_finbert_weight(features, feature_names)
        llm_weight = self._calculate_llm_weight(features, feature_names, model_type)
        
        # Normalize weights
        total_weight = finbert_weight + llm_weight
        if total_weight > 0:
            finbert_weight /= total_weight
            llm_weight /= total_weight
        else:
            finbert_weight = llm_weight = 0.5
        
        # Weighted combination
        finbert_score = finbert_result.get('numerical_score', 0)
        llm_score = second_model_result.get('numerical_score', 0)
        
        weighted_score = (finbert_score * finbert_weight + 
                         llm_score * llm_weight)
        
        # Scale to -100 to +100 for backward compatibility
        scaled_score = weighted_score * 100
        
        # Agreement metrics
        score_diff = abs(finbert_score - llm_score)
        classifications_agree = (finbert_result.get('classification') == 
                               second_model_result.get('classification'))
        
        # Enhanced confidence based on agreement and individual confidences
        finbert_conf = max(finbert_result.get('detailed_scores', {}).values()) if finbert_result.get('detailed_scores') else 0.33
        llm_detailed = second_model_result.get('detailed_scores', {})
        llm_conf = max([llm_detailed.get('positive', 0.33), 
                       llm_detailed.get('negative', 0.33), 
                       llm_detailed.get('neutral', 0.33)])
        
        # Confidence penalty for disagreement
        agreement_bonus = 0.2 if classifications_agree else -0.1
        confidence = ((finbert_conf * finbert_weight + 
                      llm_conf * llm_weight) + agreement_bonus)
        confidence = max(0.0, min(1.0, confidence))
        
        # Final classification
        if scaled_score > 10:
            classification = "bullish"
        elif scaled_score < -10:
            classification = "bearish"
        else:
            classification = "neutral"
        
        return {
            "numerical_score": scaled_score,
            "classification": classification,
            "models_agree": classifications_agree,
            "confidence": confidence,
            "agreement_rate": 1.0 if classifications_agree else 0.0,
            "model_scores": {
                "finbert": finbert_score,
                "second_model": llm_score,
            },
            "model_weights": {
                "finbert": finbert_weight,
                "second_model": llm_weight,
            },
            "features": features.tolist(),
            "feature_names": feature_names,
            "score_difference": score_diff
        }
    
    def _calculate_finbert_weight(self, features, feature_names):
        """
        Calculate FinBERT weight based on features (rule-based for now)
        """
        feature_dict = dict(zip(feature_names, features[0]))
        
        base_weight = 0.5
        
        # Boost FinBERT for financial content
        if feature_dict.get('is_financial_heavy', 0):
            base_weight += 0.3
        
        financial_density = feature_dict.get('financial_keyword_density', 0)
        base_weight += financial_density * 0.2
        
        # Boost if FinBERT is confident
        if feature_dict.get('finbert_confident', 0):
            base_weight += 0.15
        
        # Penalize if LLM is much more confident
        if (feature_dict.get('gemini_confident', 0) or 
            feature_dict.get('openai_confident', 0)) and not feature_dict.get('finbert_confident', 0):
            base_weight -= 0.1
        
        return max(0.1, min(0.9, base_weight))
    
    def _calculate_llm_weight(self, features, feature_names, model_type):
        """
        Calculate LLM weight based on features
        """
        return 1.0 - self._calculate_finbert_weight(features, feature_names)

    def analyze_sentiment(self, text, use_openai=True, news_id=None):
        """
        Enhanced sentiment analysis with feature-based integration and active learning
        """
        # Preprocess the text
        preprocessed_text = self.preprocess_text(text)

        # Split the text into manageable segments
        text_segments = self.split_text(preprocessed_text)

        # Process each segment with both models
        finbert_results = []
        second_model_results = []

        model_type = 'openai' if use_openai else 'gemini'
        
        for segment in text_segments:
            finbert_results.append(self.analyze_with_finbert(segment))
            
            if use_openai:
                second_model_results.append(self.analyze_with_openai(segment))
            else:
                second_model_results.append(self.analyze_with_gemini(segment))
        
        # Enhanced integration with features
        integrated_results = []
        for i in range(len(text_segments)):
            integrated_results.append(
                self.enhanced_weighted_integration(
                    finbert_results[i], 
                    second_model_results[i], 
                    text_segments[i],
                    model_type
                )
            )

        # Aggregate results from all segments
        if not integrated_results:
            return {
                "numerical_score": 0,
                "classification": "neutral",
                "confidence": 0,
                "segment_count": 0,
            }

        # Enhanced aggregation using confidence-weighted averaging
        total_confidence = sum(result["confidence"] for result in integrated_results)
        if total_confidence == 0:
            total_confidence = 1
        
        final_score = sum(
            result["numerical_score"] * result["confidence"]
            for result in integrated_results
        ) / total_confidence
        
        final_finbert_score = sum(
            result["model_scores"]["finbert"] * result["confidence"] * 100
            for result in integrated_results
        ) / total_confidence
        
        final_second_model_score = sum(
            result["model_scores"]["second_model"] * result["confidence"] * 100
            for result in integrated_results
        ) / total_confidence
        
        # Enhanced classification
        final_classification = ("bullish" if final_score > 10 
                              else "bearish" if final_score < -10 
                              else "neutral")
        
        # Enhanced agreement calculation
        avg_agreement_rate = sum(
            result["agreement_rate"] for result in integrated_results
        ) / len(integrated_results)
        
        avg_confidence = sum(
            result["confidence"] for result in integrated_results
        ) / len(integrated_results)
        
        # Calculate overall model weights
        avg_finbert_weight = sum(
            result["model_weights"]["finbert"] for result in integrated_results
        ) / len(integrated_results)
        
        # Calculate shap values for FinBert scores
        shap_explanation = self.get_shap_explanation(preprocessed_text)
        shap_json = self.shap_explanation_to_json(shap_explanation)
        shap_html = self.generate_shap_html(shap_explanation)

        # Upload SHAP HTML to blob storage
        import hashlib
        analysis_id = hashlib.md5(text.encode()).hexdigest()[:12]
        # shap_blob_url = upload_shap_to_blob(shap_html, analysis_id)

        # Check if this analysis should trigger human feedback
        if integrated_results:
            # Use first segment to check for disagreement
            first_segment = integrated_results[0]
            finbert_score = first_segment.get('model_scores', {}).get('finbert', 0)
            llm_score = first_segment.get('model_scores', {}).get('second_model', 0)
            
            # Construct minimal model-result dicts used by the selector
            finbert_result = {'numerical_score': finbert_score, 'classification': 'neutral', 'detailed_scores': {}}
            llm_result = {'numerical_score': llm_score, 'classification': 'neutral', 'detailed_scores': {}}
            
            # Log the raw values used for disagreement/uncertainty calculation
            logger.info(
                "Auto-enqueue check (news_id=%s) first_segment model_scores: finbert=%s, llm=%s",
                news_id,
                finbert_score,
                llm_score,
            )
            logger.debug("Auto-enqueue first_segment full content: %s", json.dumps(first_segment, default=str)[:4000])

            features = first_segment.get('features', [])
            feature_names = first_segment.get('feature_names', [])
            features_dict = dict(zip(feature_names, features)) if len(feature_names) == len(features) else {}
            
            needs_human_feedback = should_request_human_feedback(
                finbert_result, llm_result, preprocessed_text, features_dict
            )
            logger.info(
                "should_request_human_feedback result for news_id=%s -> %s (disagreement/uncertainty will be logged in selector)",
                news_id,
                needs_human_feedback,
            )
            
            # AUTO-ENQUEUE: If disagreement detected, add to labeling queue
            if needs_human_feedback and news_id:
                try:
                    self._auto_enqueue_for_labeling(
                        news_id=news_id,
                        text=preprocessed_text,
                        finbert_result=finbert_result,
                        llm_result=llm_result,
                        model_type=model_type,
                        features=features,
                        feature_names=feature_names
                    )
                    logger.info(f"Auto-enqueued news {news_id} for human labeling due to model disagreement")
                except Exception as e:
                    logger.error(f"Failed to auto-enqueue disagreement case: {e}")
        else:
            needs_human_feedback = False

        return {
            "numerical_score": final_score,
            "finbert_score": final_finbert_score,
            "second_model_score": final_second_model_score,
            "classification": final_classification,
            "confidence": avg_confidence,
            "agreement_rate": avg_agreement_rate,
            "segment_count": len(text_segments),
            "segment_results": integrated_results,
            "shap": shap_json,
            "shap_html": shap_html,
            "model_type_used": model_type,
            "model_weights": {
                "finbert": avg_finbert_weight,
                "second_model": 1.0 - avg_finbert_weight
            },
            "enhanced_features": True,
            "needs_human_feedback": needs_human_feedback,
            "disagreement_detected": avg_agreement_rate < 0.7  # Flag for UI
        }

    def _auto_enqueue_for_labeling(self, news_id, text, finbert_result, llm_result, 
                                  model_type, features, feature_names):
        """
        Automatically enqueue high-disagreement cases for human labeling
        """
        try:
            # Create active learning selector to calculate metrics
            selector = ActiveLearningSelector()
            # Log inputs just before selector runs
            logger.info(
                "Running selector for auto-enqueue (news_id=%s) with finbert=%s llm=%s",
                news_id,
                finbert_result.get("numerical_score"),
                llm_result.get("numerical_score"),
            )
            disagreement_score = selector.calculate_disagreement_score(finbert_result, llm_result)
            uncertainty_score = selector.calculate_uncertainty_score(finbert_result, llm_result)
            logger.info(
                "Selector results (news_id=%s): disagreement_score=%.4f uncertainty_score=%.4f",
                news_id,
                disagreement_score,
                uncertainty_score,
            )
            
            # Determine priority and reason
            features_dict = dict(zip(feature_names, features)) if len(feature_names) == len(features) else {}
            should_sample, reason, priority = selector.should_sample_for_disagreement(
                disagreement_score, uncertainty_score, features_dict
            )
            logger.info(
                "Selector decision (news_id=%s): should_sample=%s reason=%s priority=%s features_keys=%s",
                news_id,
                should_sample,
                reason,
                priority,
                list(features_dict.keys())[:20],
            )
            
            if not should_sample:
                # Try uncertainty sampling as fallback
                near_neutral = selector.calculate_near_neutral_score(finbert_result, llm_result)
                should_sample, reason, priority = selector.should_sample_for_uncertainty(
                    uncertainty_score, near_neutral, features_dict
                )
            
            if should_sample:
                # Handle both UUID and integer news IDs
                news_id_for_storage = news_id
                if isinstance(news_id, str):
                    # If it's a UUID string, store it as string in a text field
                    # We'll need to modify the model to handle this properly
                    try:
                        # Try to convert to int first for backward compatibility
                        news_id_for_storage = int(news_id)
                    except ValueError:
                        # Store UUID as string - will need model update
                        news_id_for_storage = str(news_id)
                
                # Prepare queue item data
                queue_data = {
                    'news_id': news_id_for_storage,
                    'text': text,
                    'finbert_score': finbert_result['numerical_score'],
                    'llm_score': llm_result['numerical_score'],
                    'model_type': model_type,
                    'disagreement_score': disagreement_score,
                    'uncertainty_score': uncertainty_score,
                    'sampling_reason': reason,
                    'priority': priority,
                    'features_json': features.tolist() if hasattr(features, 'tolist') else [],
                    'feature_names_json': feature_names
                }
                
                # Make internal API call to enqueue
                from flask import current_app
                with current_app.test_client() as client:
                    response = client.post('/api/labeling/enqueue', 
                                         json=queue_data,
                                         content_type='application/json')
                    
                    if response.status_code != 201:
                        logger.error(f"Failed to enqueue item: {response.get_json()}")
                    else:
                        logger.info(f"Successfully enqueued disagreement case with priority {priority}")
                        
        except Exception as e:
            logger.error(f"Error in auto-enqueue process: {e}")
            # Don't raise - this is a background enhancement, shouldn't break main flow

# ...existing code...

def get_sentiment(text, use_openai=True, use_gemini=False, news_id=None):
    """
    Analyze the sentiment of a financial text using the SentimentAnalyzer

    Parameters:
    - text: The text to analyze
    - use_openai: Whether to use OpenAI as the second model (if False, uses Gemini)
    - use_gemini: Whether to use Gemini as the second model (if False, uses OpenAI)
    - news_id: Optional news ID for auto-enqueueing disagreement cases
    Returns a dictionary with sentiment analysis results
    """
    analyzer = SentimentAnalyzer()

    if use_openai and use_gemini:
        # Analyze with both models
        result_with_open_ai = analyzer.analyze_sentiment(text, use_openai=True, news_id=news_id)
        result_with_gemini = analyzer.analyze_sentiment(text, use_openai=False, news_id=news_id)

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
        result = analyzer.analyze_sentiment(text, use_openai=False, news_id=news_id)

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
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    sample_text = """
    Tesla reported strong Q4 earnings, beating analyst expectations with revenue growth of 13% year-over-year. 
    The company's automotive gross margins improved to 21.6%, and the company expects to increase production significantly in 2025.
    However, some analysts remain concerned about increasing competition in the electric vehicle market.
    """

    # Test with just FinBERT for simplicity
    finbert_only = analyzer.analyze_with_finbert(sample_text)

    explainer = shap.Explainer(analyzer.finbert_pipeline)
    explanation = explainer([sample_text])
    json_data = shap_explanation_to_json(explanation)
    print(json_data)
    print(explanation[:2])
    shap.plots.text(shap_values[0], display=False)  # Get HTML object
    html = shap.plots.text(shap_values[0], display=False)
    with open("shap_text_explanation.html", "w") as f:
        f.write(html)  # No .data needed

    # shap.save_html(str(out_path), html)
    print("=== FinBERT Analysis Only ===")
    print(f"Sentiment: {finbert_only['classification']}")
    print(f"Score: {finbert_only['numerical_score']:.2f}")
    print(f"Details: {finbert_only['detailed_scores']}")

    # Uncomment to test with Gemini (replace YOUR_GEMINI_API_KEY_HERE with your actual key)
    """
    # Compare FinBERT + Gemini results
    gemini_result = analyzer.analyze_sentiment(sample_text, use_openai=False)
    
    print("\n=== FinBERT + Gemini Analysis ===")
    print(f"Sentiment: {gemini_result['classification']}")
    print(f"Score: {gemini_result['numerical_score']:.2f}")
    print(f"Confidence: {gemini_result['confidence']:.2f}")
    print(f"Agreement rate: {gemini_result['agreement_rate']:.2f}")
    print(f"Segments analyzed: {gemini_result['segment_count']}")
    """

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
