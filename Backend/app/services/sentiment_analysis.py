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
import numpy as np
from app.services.sentiment.active_learning import should_request_human_feedback, ActiveLearningSelector

from app.utils.helpers import upload_shap_to_blob
from app.services.sentiment.features import SentimentFeatureBuilder

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_SEGMENT_LENGTH = 512  # Maximum length for text segments
AGREEMENT_THRESHOLD = 0.7  # 70% agreement required between models
SENTIMENT_THRESHOLD = 0.1  # Threshold for determining positive/negative sentiment

# load environment variables
load_dotenv()


class SentimentAnalyzer:
    def __init__(self):
        self._finbert_pipeline = None
        self.gemini_client = None
        self.feature_builder = SentimentFeatureBuilder()
        self._meta_classifier = None  # NEW: Lazy-load trained meta-classifier
    
    @property
    def finbert_pipeline(self):
        """Lazy load FinBERT model on first access"""
        if self._finbert_pipeline is None:
            logger.info("Loading FinBERT model on first use...")
            self._finbert_pipeline = self._load_finbert()
            logger.info("FinBERT model loaded successfully")
        return self._finbert_pipeline

    @property
    def meta_classifier(self):
        """Lazy load meta-classifier model"""
        if self._meta_classifier is None:
            self._load_meta_classifier()
        return self._meta_classifier

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

    def _load_meta_classifier(self):
        """Load the active meta-classifier from disk"""
        try:
            from flask import current_app
            from app.models.active_learning import ModelRun
            
            with current_app.app_context():
                # Get active model
                active_model = ModelRun.query.filter_by(is_active=True).first()
                
                if not active_model:
                    logger.warning("No active meta-classifier found. Using rule-based integration.")
                    return None
                
                # Load model
                import joblib
                model_data = joblib.load(active_model.artifact_path)
                self._meta_classifier = model_data
                
                logger.info(f"Loaded meta-classifier: {active_model.model_version}")
                logger.info(f"Model accuracy: {model_data['metrics'].get('accuracy', 'N/A')}")
                
        except Exception as e:
            logger.warning(f"Failed to load meta-classifier: {e}. Falling back to rule-based.")
            self._meta_classifier = None

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

    def _validate_numeric(self, value: float, default: float = 0.0) -> float:
        """Validate and return safe numeric value"""
        if value is None or np.isnan(value) or np.isinf(value):
            return default
        return float(value)

    def analyze_with_finbert(self, text):
        """
        Analyze sentiment using FinBERT model with improved error handling
        """
        if not text or len(text.strip()) < 5:
            logger.warning("Empty or very short text passed to FinBERT.")
            return {
                "numerical_score": 0.0,
                "classification": "neutral",
                "detailed_scores": {"positive": 0.33, "negative": 0.33, "neutral": 0.34},
            }

        try:
            # Run model inference
            results = self.finbert_pipeline(text)

            # Validate structure
            if not results or not isinstance(results, list):
                logger.warning("FinBERT returned empty or malformed results.")
                return self._get_default_sentiment_result()

            # Extract label scores
            scores_dict = {}
            for item in results:
                if isinstance(item, dict) and 'label' in item and 'score' in item:
                    label = item['label'].lower()
                    score = float(item['score'])
                    if np.isnan(score) or np.isinf(score):
                        continue
                    scores_dict[label] = score

            # Default fallback values
            positive_score = scores_dict.get('positive', 0.33)
            negative_score = scores_dict.get('negative', 0.33)
            neutral_score  = scores_dict.get('neutral', 0.34)

            # Normalize safely
            total = positive_score + negative_score + neutral_score
            if total <= 0 or np.isnan(total) or np.isinf(total):
                positive_score = negative_score = neutral_score = 1 / 3
                total = 1.0

            positive_score /= total
            negative_score /= total
            neutral_score  /= total

            # Compute numeric sentiment
            numerical_score = positive_score - negative_score
            numerical_score = float(np.clip(numerical_score, -1.0, 1.0))

            # ✅ Log debug info
            logger.debug(f"FinBERT raw: pos={positive_score:.3f}, neg={negative_score:.3f}, neu={neutral_score:.3f}, num={numerical_score:.3f}")

            # Classification threshold
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
                    "positive": positive_score,
                    "negative": negative_score,
                    "neutral": neutral_score,
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing with FinBERT: {e}", exc_info=True)
            return self._get_default_sentiment_result()
    
    def _get_default_sentiment_result(self):
        """Return a safe default sentiment result when models fail"""
        return {
            "numerical_score": 0.0,
            "classification": "neutral",
            "detailed_scores": {
                'positive': 0.33,
                'negative': 0.33,
                'neutral': 0.34,
                'overall': 0.5  
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
            numerical_score = self._validate_numeric(numerical_score)

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
                "model": "gpt-4o-mini",  # Updated model name (gpt-4-turbo-preview deprecated)
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
            numerical_score = self._validate_numeric(numerical_score)

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

    def _build_features_dict(self, features, feature_names):
        """Safely build feature dictionary with validation and automatic shape alignment"""
        import numpy as np

        # Basic sanity check
        if feature_names is None or features is None:
            logger.warning("Feature builder received None values.")
            return {}

        # Convert numpy arrays safely
        if isinstance(features, np.ndarray):
            features = features.squeeze()  # remove singleton dims like (1, n) or (n, 1)
            if features.ndim == 0:
                # single scalar (not a vector)
                features = [float(features)]
            else:
                features = features.tolist()

        # Handle plain scalar (e.g., float or int)
        if isinstance(features, (float, int)):
            features = [float(features)]

        # Handle nested lists (e.g., [[0.2, 0.3]])
        if isinstance(features, list) and len(features) == 1 and isinstance(features[0], list):
            features = features[0]

        # Final validation
        if len(feature_names) != len(features):
            logger.warning(f"Feature mismatch: {len(feature_names)} names vs {len(features)} values")
            min_len = min(len(feature_names), len(features))
            feature_names = feature_names[:min_len]
            features = features[:min_len]

        # Zip safely
        features_dict = dict(zip(feature_names, features))
        logger.debug(f"Built features_dict with {len(features_dict)} entries")
        return features_dict

    def enhanced_weighted_integration(self, finbert_result, second_model_result, text, model_type='gemini'):
        """
        Enhanced integration with optional meta-classifier prediction
        """
        # 1. Build features for this sample
        features, feature_names = self.feature_builder.build_single_sample_features(
            finbert_result, second_model_result, text, model_type
        )
        
        features_dict = self._build_features_dict(features, feature_names)
        
        # 2. Try meta-classifier prediction if available
        if self.meta_classifier:
            try:
                # Prepare feature vector matching training schema
                model_feature_names = self.meta_classifier['feature_names']
                
                # Build feature vector in SAME ORDER as training
                feature_vector = np.array([
                    features_dict.get(fname, 0.0) for fname in model_feature_names
                ])
                
                # Validate feature vector
                if len(feature_vector) != len(model_feature_names):
                    raise ValueError(
                        f"Feature count mismatch: got {len(feature_vector)}, expected {len(model_feature_names)}"
                    )
                
                # Check for invalid values
                if np.any(np.isnan(feature_vector)) or np.any(np.isinf(feature_vector)):
                    logger.warning("Invalid values in feature vector, replacing with 0")
                    feature_vector = np.nan_to_num(feature_vector, 0.0)
                
                feature_vector = feature_vector.reshape(1, -1)
                
                # Predict sentiment
                prediction = self.meta_classifier['model'].predict(feature_vector)[0]
                
                # Get prediction probabilities for confidence
                if hasattr(self.meta_classifier['model'], 'predict_proba'):
                    probas = self.meta_classifier['model'].predict_proba(feature_vector)[0]
                    confidence = float(max(probas))
                else:
                    confidence = 0.75  # Default confidence for non-probabilistic models
                
                # Convert prediction to classification
                label_map = {1: 'bullish', 0: 'neutral', -1: 'bearish'}
                classification = label_map.get(prediction, 'neutral')
                
                # Scale to -100 to +100
                scaled_score = prediction * 100
                
                logger.info(
                    f"✓ Meta-classifier prediction: {classification} "
                    f"(score: {scaled_score:.2f}, confidence: {confidence:.2f})"
                )
                
                # FIX: Return complete dict matching rule-based integration schema
                return {
                    "numerical_score": scaled_score,
                    "classification": classification,
                    "models_agree": True,  # Meta-classifier makes final decision
                    "confidence": confidence,
                    "agreement_rate": 1.0,  # Single prediction
                    "model_scores": {
                        "finbert": finbert_result["numerical_score"],
                        "second_model": second_model_result["numerical_score"],
                    },
                    "model_weights": {
                        "finbert": 0.0,  # Meta-classifier overrides weights
                        "second_model": 0.0,
                        "meta_classifier": 1.0
                    },
                    # FIX: Add missing fields expected downstream
                    "confidence_weights": {
                        "finbert": 0.0,
                        "second_model": 0.0,
                    },
                    "model_confidences": {
                        "finbert": features_dict.get('finbert_confidence', 0.5),
                        "second_model": features_dict.get(f'{model_type}_confidence', 0.5),
                    },
                    "features": features.tolist(),
                    "feature_names": feature_names,
                    "score_difference": features_dict.get('score_difference', 0),
                    "magnitude": {
                        "finbert": features_dict.get('finbert_magnitude', 0),
                        "second_model": features_dict.get(f'{model_type}_magnitude', 0),
                    },
                    "both_confident": features_dict.get('both_confident', 0),
                    "neither_confident": features_dict.get('neither_confident', 0),
                    "needs_human_labeling": False,  # Confident meta-classifier prediction
                    "integration_reason": "meta_classifier_prediction"
                }
                
            except Exception as e:
                logger.warning(f"Meta-classifier prediction failed: {e}. Falling back to rule-based integration.")
        
        # Extract key metrics (is classification agreeable?)
        classifications_agree = (finbert_result.get('classification') == 
                               second_model_result.get('classification'))
        
        # Calculate confidence scores properly - use features if available
        finbert_confidence = features_dict.get('finbert_confidence', 0.33)
        llm_confidence = features_dict.get(f'{model_type}_confidence', 0.33)
        
        # Fallback to manual calculation if features missing
        if finbert_confidence == 0.33:
            finbert_detailed = finbert_result.get('detailed_scores', {})
            finbert_confidence = max(
                finbert_detailed.get('positive', 0.33),
                finbert_detailed.get('negative', 0.33),
                finbert_detailed.get('neutral', 0.33)
            )
        
        if llm_confidence == 0.33:
            llm_detailed = second_model_result.get('detailed_scores', {})
            llm_confidence = max(
                llm_detailed.get('positive', 0.33),
                llm_detailed.get('negative', 0.33),
                llm_detailed.get('neutral', 0.33)
            )
        
        # Ensure valid confidence values
        finbert_confidence = max(0.0, min(1.0, finbert_confidence))
        llm_confidence = max(0.0, min(1.0, llm_confidence))
        
        both_confident = int(finbert_confidence > 0.5 and llm_confidence > 0.5)
        neither_confident = int(finbert_confidence <= 0.5 and llm_confidence <= 0.5)
        
        # Calculate score difference and magnitude - use features if available
        finbert_score = features_dict.get('finbert_raw_score', finbert_result.get('numerical_score', 0))
        llm_score = features_dict.get(f'{model_type}_raw_score', second_model_result.get('numerical_score', 0))
        
        # Ensure valid scores
        finbert_score = self._validate_numeric(finbert_score)
        llm_score = self._validate_numeric(llm_score)
        
        score_diff = features_dict.get('score_difference', abs(finbert_score - llm_score))
        
        # Magnitude (how far from neutral)
        finbert_magnitude = features_dict.get('finbert_magnitude', abs(finbert_score))
        llm_magnitude = features_dict.get(f'{model_type}_magnitude', abs(llm_score))
        
        # --- RULE-BASED INTEGRATION (stepping stone to meta-classifier) ---
        is_financial_heavy = features_dict.get('is_financial_heavy', 0)
        needs_human_labeling = False
        integration_reason = "standard"
                
        # Rule 1: Financial-heavy content - prioritize FinBERT
        if is_financial_heavy == 1:
            finbert_weight = 0.75
            llm_weight = 0.25
            integration_reason = "financial_heavy_finbert_priority"
        
        # Rule 2: Models agree AND both confident - accept consensus
        elif classifications_agree and both_confident == 1:
            finbert_weight = 0.5 
            llm_weight = 0.5
            integration_reason = "confident_consensus"
        
        # Rule 3: High disagreement with confidence - mark for human labeling
        elif score_diff > 0.4 and both_confident == 1:
            finbert_weight = 0.5
            llm_weight = 0.5
            needs_human_labeling = True
            integration_reason = "high_disagreement_confident"
        
        # Rule 4: Classifications disagree AND both confident - active learning priority
        elif not classifications_agree and both_confident == 1:
            finbert_weight = 0.5
            llm_weight = 0.5
            needs_human_labeling = True
            integration_reason = "classification_disagreement_confident"
        
        # Rule 5: Neither model confident - mark for human review
        elif neither_confident == 1:
            finbert_weight = 0.5
            llm_weight = 0.5
            needs_human_labeling = True
            integration_reason = "low_confidence_both"
        
        # Rule 6: High score difference regardless of confidence
        elif score_diff > 0.6:
            finbert_weight = 0.5
            llm_weight = 0.5
            needs_human_labeling = True
            integration_reason = "extreme_disagreement"
        
        # Default: Use feature-based weighting
        else:
            finbert_weight = 0.5
            
            if is_financial_heavy:
                finbert_weight += 0.3
            
            financial_density = features_dict.get('financial_keyword_density', 0)
            finbert_weight += financial_density * 0.2
            
            if features_dict.get('finbert_confident', 0):
                finbert_weight += 0.15
            
            # Clamp to valid range
            finbert_weight = max(0.1, min(0.9, finbert_weight))
            llm_weight = 1.0 - finbert_weight
            integration_reason = "feature_based"
        
        # --- CONFIDENCE-BASED WEIGHTING ---
        # Apply confidence as additional weight when combining scores
        finbert_conf_weight = finbert_confidence * finbert_weight
        llm_conf_weight = llm_confidence * llm_weight
        
        total_conf_weight = finbert_conf_weight + llm_conf_weight
        if total_conf_weight > 0:
            finbert_conf_weight /= total_conf_weight
            llm_conf_weight /= total_conf_weight
        else:
            finbert_conf_weight = llm_conf_weight = 0.5
        
        # Weighted combination using confidence-weighted scores
        weighted_score = (finbert_score * finbert_conf_weight + 
                         llm_score * llm_conf_weight)
        
        # Ensure valid weighted score
        weighted_score = self._validate_numeric(weighted_score)
        
        # Scale to -100 to +100 for backward compatibility
        scaled_score = weighted_score * 100
        
        # Enhanced confidence metric
        # Agreement bonus for classification agreement
        agreement_bonus = 0.2 if classifications_agree else -0.15
        
        # Base confidence from weighted model confidences
        base_confidence = (finbert_confidence * finbert_weight + 
                          llm_confidence * llm_weight)
        
        # Penalize for disagreement
        disagreement_penalty = min(score_diff * 0.3, 0.5)  # Cap penalty at 0.5
        
        final_confidence = base_confidence + agreement_bonus - disagreement_penalty
        final_confidence = max(0.0, min(1.0, final_confidence))
        
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
            "confidence": final_confidence,
            "agreement_rate": 1.0 if classifications_agree else 0.0,
            "model_scores": {
                "finbert": finbert_result["numerical_score"],
                "second_model": second_model_result["numerical_score"],
            },
            "model_weights": {
                "finbert": finbert_weight,
                "second_model": llm_weight,
            },
            "confidence_weights": {
                "finbert": finbert_conf_weight,
                "second_model": llm_conf_weight,
            },
            "model_confidences": {
                "finbert": finbert_confidence,
                "second_model": llm_confidence,
            },
            "features": features.tolist(),
            "feature_names": feature_names,
            "score_difference": score_diff,
            "magnitude": {
                "finbert": finbert_magnitude,
                "second_model": llm_magnitude,
            },
            "both_confident": both_confident,
            "neither_confident": neither_confident,
            "needs_human_labeling": needs_human_labeling,
            "integration_reason": integration_reason,
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

    def analyze_sentiment(self, text, use_openai=True, news_id=None):
        """
        Enhanced sentiment analysis with feature-based integration and active learning
        """
        # Preprocess the text
        preprocessed_text = self.preprocess_text(text)

        # Split the text into manageable segments
        text_segments = self.split_text(preprocessed_text)

        # Process each segment with both models (with graceful error handling)
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
                "numerical_score": 0.0,
                "classification": "neutral",
                "confidence": 0.0,
                "segment_count": 0,
                #new
                "finbert_score": 0.0,
                "second_model_score": 0.0,
                "agreement_rate": 0.0,
                "model_weights": {"finbert": 0.5, "second_model": 0.5},
                "enhanced_features": True,
                "needs_human_feedback": False,
                "disagreement_detected": False,
                "rule_based_integration": True,
                "any_segment_needs_labeling": False,
                "shap": None,
                "shap_html": None,
            }

        # Enhanced aggregation using confidence-weighted averaging
        total_confidence = sum(result["confidence"] for result in integrated_results)
        if total_confidence == 0:
            total_confidence = 1
        
        final_score = sum(
            result["numerical_score"] * result["confidence"]
            for result in integrated_results
        ) / total_confidence
        
        # Ensure valid final score for News model storage
        final_score = self._validate_numeric(final_score)
        
        final_finbert_score = sum(
            result["model_scores"]["finbert"] * result["confidence"] * 100
            for result in integrated_results
        ) / total_confidence
        
        # Ensure valid finbert score for News model
        final_finbert_score = self._validate_numeric(final_finbert_score)
        
        final_second_model_score = sum(
            result["model_scores"]["second_model"] * result["confidence"] * 100
            for result in integrated_results
        ) / total_confidence
        
        # Ensure valid second model score for News model
        final_second_model_score = self._validate_numeric(final_second_model_score)
        
        # Calculate average weights for reporting
        avg_finbert_weight = sum(
            result["model_weights"]["finbert"] for result in integrated_results
        ) / len(integrated_results)
        
        # Enhanced classification
        final_classification = ("bullish" if final_score > 10 
                              else "bearish" if final_score < -10 
                              else "neutral")
        
        # Enhanced agreement calculation
        avg_agreement_rate = sum(
            result["agreement_rate"] for result in integrated_results
        ) / len(integrated_results)
        
        # Ensure valid agreement rate for News model
        avg_agreement_rate = self._validate_numeric(avg_agreement_rate)
        
        avg_confidence = sum(
            result["confidence"] for result in integrated_results
        ) / len(integrated_results)
        
        # Ensure valid confidence for News model
        avg_confidence = self._validate_numeric(avg_confidence)
        
        # Aggregate human labeling flags
        any_needs_human_labeling = any(
            result.get("needs_human_labeling", False) for result in integrated_results
        )

        shap_json = None
        shap_html = None
        try:
            shap_explanation = self.get_shap_explanation(preprocessed_text)
            shap_json = self.shap_explanation_to_json(shap_explanation)
            shap_html = self.generate_shap_html(shap_explanation)
        except Exception as e:
            logger.warning(f"SHAP generation failed (non-critical): {str(e)}")
            # Continue without SHAP - it's not critical for sentiment analysis


        # Check if this analysis should trigger human feedback
        if integrated_results:
            # Use first segment to check for disagreement
            first_segment = integrated_results[0]
            
            # Check rule-based needs_human_labeling flag first
            needs_human_feedback = first_segment.get("needs_human_labeling", False)
            
            # If not flagged by rules, check active learning criteria
            if not needs_human_feedback:
                finbert_score = first_segment.get('model_scores', {}).get('finbert', 0)
                llm_score = first_segment.get('model_scores', {}).get('second_model', 0)
                
                finbert_result = {
                    'numerical_score': finbert_score, 
                    'classification': 'neutral', 
                    'detailed_scores': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
                }
                llm_result = {
                    'numerical_score': llm_score, 
                    'classification': 'neutral', 
                    'detailed_scores': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
                }
                
                logger.info(
                    "Auto-enqueue check (news_id=%s) first_segment model_scores: finbert=%s, llm=%s",
                    news_id,
                    finbert_score,
                    llm_score,
                )

                features = first_segment.get('features', [])
                feature_names = first_segment.get('feature_names', [])
                features_dict = self._build_features_dict(features, feature_names)
                
                needs_human_feedback = should_request_human_feedback(
                    finbert_result, llm_result, preprocessed_text, features_dict
                )
            
            logger.info(
                "Final needs_human_feedback for news_id=%s -> %s (reason: %s)",
                news_id,
                needs_human_feedback,
                first_segment.get("integration_reason", "unknown")
            )
            
            # AUTO-ENQUEUE: If disagreement detected, add to labeling queue
            if needs_human_feedback and news_id:
                try:
                    finbert_score = first_segment.get('model_scores', {}).get('finbert', 0)
                    llm_score = first_segment.get('model_scores', {}).get('second_model', 0)
                    finbert_result = {
                        'numerical_score': finbert_score, 
                        'classification': 'neutral', 
                        'detailed_scores': {}
                    }
                    llm_result = {
                        'numerical_score': llm_score, 
                        'classification': 'neutral', 
                        'detailed_scores': {}
                    }
                    features = first_segment.get('features', [])
                    feature_names = first_segment.get('feature_names', [])
                    
                    self._auto_enqueue_for_labeling(
                        news_id=news_id,
                        text=preprocessed_text,
                        finbert_result=finbert_result,
                        llm_result=llm_result,
                        model_type=model_type,
                        features=features,
                        feature_names=feature_names,
                        segment_result=first_segment,
                    )
                    logger.info(f"Auto-enqueued news {news_id} for human labeling (reason: {first_segment.get('integration_reason')})")
                except Exception as e:
                    logger.error(f"Failed to auto-enqueue disagreement case: {e}")
        else:
            needs_human_feedback = False
            any_needs_human_labeling = False

        # After getting integrated_results:
        first_segment = integrated_results[0] if integrated_results else {}
        
        return {
            "numerical_score": float(final_score),
            "finbert_score": float(final_finbert_score),
            "second_model_score": float(final_second_model_score),
            "classification": final_classification,
            "confidence": float(avg_confidence),
            "agreement_rate": float(avg_agreement_rate),
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
            "disagreement_detected": avg_agreement_rate < 0.7,
            "rule_based_integration": True,
            "any_segment_needs_labeling": any_needs_human_labeling,
        }

    def _auto_enqueue_for_labeling(self, news_id, text, finbert_result, llm_result, 
                                  model_type, features, feature_names, segment_result):
        """
        Automatically enqueue high-disagreement cases for human labeling
        """
        try:
            # Create active learning selector to calculate metrics
            selector = ActiveLearningSelector()
            logger.info(
                "Running selector for auto-enqueue (news_id=%s) with finbert=%s llm=%s",
                news_id,
                finbert_result.get("numerical_score"),
                llm_result.get("numerical_score"),
            )
            disagreement_score = selector.calculate_disagreement_score(finbert_result, llm_result)
            uncertainty_score = selector.calculate_uncertainty_score(finbert_result, llm_result)

            # Determine priority and reason
            features_dict = self._build_features_dict(features, feature_names)
            should_sample, reason, priority = selector.should_sample_for_disagreement(
                disagreement_score, uncertainty_score, features_dict
            )
            
            if not should_sample:
                # Try uncertainty sampling as fallback
                near_neutral = selector.calculate_near_neutral_score(finbert_result, llm_result)
                should_sample, reason, priority = selector.should_sample_for_uncertainty(
                    uncertainty_score, near_neutral, features_dict
                )
                
            # Ensure features is JSON-serializable
            features_json = []
            if isinstance(features, np.ndarray):
                features_json = features.tolist()
            elif isinstance(features, (list, tuple)):
                features_json = list(features)
            
            if should_sample:
                # Convert news_id to string for LabelingQueue.news_id
                news_id_str = str(news_id) if news_id else None
                
                # Prepare queue item data with enhanced fields
                queue_data = {
                    'news_id': news_id_str,
                    'text': text[:5000],
                    'finbert_score': float(finbert_result['numerical_score']),
                    'llm_score': float(llm_result['numerical_score']),
                    'model_type': model_type,
                    'disagreement_score': float(disagreement_score),
                    'uncertainty_score': float(uncertainty_score),
                    'sampling_reason': reason,
                    'priority': int(priority),
                    'features_json': list(feature_names) if feature_names else [],
                    'feature_names_json': list(feature_names) if feature_names else [],
                    # NEW: Enhanced metadata
                    'model_weights': segment_result.get('model_weights'),
                    'integration_reason': segment_result.get('integration_reason'),
                    'finbert_confidence': float(segment_result.get('model_confidences', {}).get('finbert', 0.33)),
                    'llm_confidence': float(segment_result.get('model_confidences', {}).get('second_model', 0.33)),
                    'both_confident': segment_result.get('both_confident') == 1,
                    'is_financial_heavy': features_dict.get('is_financial_heavy', 0) == 1,
                    'final_combined_score': float(segment_result.get('numerical_score', 0.0)),
                }
                from flask import current_app
                with current_app.test_client() as client:
                    response = client.post('/api/labeling/enqueue',     json=queue_data,
                                         content_type='application/json')
                    
                    if response.status_code != 201:
                        logger.error(f"Failed to enqueue item: {response.get_json()}")
                    else:
                        logger.info(f"Successfully enqueued disagreement case with priority {priority}")
        except Exception as e:
            logger.error(f"Error in auto-enqueue process: {e}")

def get_sentiment(text, use_openai=True, use_gemini=False, news_id=None):
    """
    Analyze the sentiment of a financial text using the SentimentAnalyzer
    with graceful degradation if models fail.

    Parameters:
    - text: The text to analyze
    - use_openai: Whether to use OpenAI as the second model (default: True)
    - use_gemini: Whether to use Gemini as the second model (default: False)
    - news_id: Optional news ID for auto-enqueueing disagreement cases
    
    Returns a dictionary with sentiment analysis results.
    Will use at least 2 models if available, degrading gracefully if models fail.
    """
    analyzer = SentimentAnalyzer()

    if use_openai and use_gemini:
        # Analyze with both models
        result_with_open_ai = analyzer.analyze_sentiment(text, use_openai=True, news_id=news_id)
        result_with_gemini = analyzer.analyze_sentiment(text, use_openai=False, news_id=news_id)

        # Combine results
        result = {
            "numerical_score": (result_with_open_ai["numerical_score"] + result_with_gemini["numerical_score"]) / 2,
            "finbert_score": (result_with_open_ai["finbert_score"] + result_with_gemini["finbert_score"]) / 2,
            "second_model_score": result_with_gemini["second_model_score"],
            "third_model_score": result_with_open_ai["second_model_score"],
            "confidence": (result_with_open_ai["confidence"] + result_with_gemini["confidence"]) / 2,
            "agreement_rate": (result_with_open_ai["agreement_rate"] + result_with_gemini["agreement_rate"]) / 2,
            "shap": result_with_open_ai.get("shap"),
            "shap_html": result_with_open_ai.get("shap_html")
        }

        # Determine classification
        if result["numerical_score"] > 10:
            result["classification"] = "bullish"
        elif result["numerical_score"] < -10:
            result["classification"] = "bearish"
        else:
            result["classification"] = "neutral"

        return result

    elif use_gemini or not use_openai:
        # Analyze with Gemini (explicit request or fallback)
        result = analyzer.analyze_sentiment(text, use_openai=False, news_id=news_id)
    else:
        # Default: Analyze with OpenAI
        result = analyzer.analyze_sentiment(text, use_openai=True, news_id=news_id)

    # Return a simplified result object for external use
    return {
        "numerical_score": result["numerical_score"],
        "finbert_score": result["finbert_score"],
        "second_model_score": result["second_model_score"],
        "third_model_score": 0,
        "classification": result["classification"],
        "confidence": result["confidence"],
        "agreement_rate": result["agreement_rate"],
        "shap": result.get("shap"),
        "shap_html": result.get("shap_html")
    }

def run_full_analysis(self, text: str, title: str = "", news_id: str = None):
    """
    Minimal wrapper so callers (like the cron job) can:
    - run both models
    - get integrated result
    - optionally auto-enqueue WITH news_id
    - get a DB-friendly payload back
    """
    full_text = f"{title}\n\n{text}" if title else text

    # 1) base model runs
    finbert_result = self.analyze_with_finbert(full_text)
    llm_result = self.analyze_with_gemini(full_text)

    # 2) integrate using your existing logic
    integrated = self.enhanced_weighted_integration(
        finbert_result,
        llm_result,
        full_text,
        model_type="gemini",
    )

    # extract numbers in the same shape as your DB expects (-100..100)
    combined_score = float(integrated.get("numerical_score", 0.0))
    classification = integrated.get("classification", "neutral")
    confidence = float(integrated.get("confidence", 0.0))
    agreement_rate = float(integrated.get("agreement_rate", 0.0))

    # 3) build features, run selector, and enqueue if needed
    selector = ActiveLearningSelector()
    disagreement_score = selector.calculate_disagreement_score(finbert_result, llm_result)
    uncertainty_score = selector.calculate_uncertainty_score(finbert_result, llm_result)
    features, feature_names = self.feature_builder.build_single_sample_features(
        finbert_result,
        llm_result,
        full_text,
        model_type="gemini",
    )
    features_dict = self._build_features_dict(features, feature_names)

    should_sample, sampling_reason, priority = selector.should_sample_for_disagreement(
        disagreement_score,
        uncertainty_score,
        features_dict,
    )

    if should_sample:
        try:
            from app import db
            from app.models.active_learning import LabelingQueue, QueueStatus

            queue_item = LabelingQueue(
                news_id=str(news_id) if news_id else None,  # ✅ attach news_id here
                text=full_text[:512],
                finbert_score=finbert_result.get("numerical_score", 0.0),
                llm_score=llm_result.get("numerical_score", 0.0),
                model_type="gemini",
                disagreement_score=disagreement_score,
                uncertainty_score=uncertainty_score,
                sampling_reason=sampling_reason,
                priority=priority,
                status=QueueStatus.PENDING,
                features_json=features.tolist() if hasattr(features, "tolist") else features_dict,
                feature_names_json=feature_names,
                final_combined_score=combined_score,
            )
            db.session.add(queue_item)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Auto-enqueue failed: {e}")

    # 4) hand back values the News row can store
    return {
        "classification": classification,
        "combined_score": combined_score,
        "confidence": confidence,
        "finbert_score": finbert_result.get("numerical_score", 0.0) * 100.0,
        "second_model_score": llm_result.get("numerical_score", 0.0) * 100.0,
        "agreement_rate": agreement_rate,
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