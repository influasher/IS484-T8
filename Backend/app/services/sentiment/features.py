import numpy as np
import logging
from typing import Dict, List, Tuple
import json

logger = logging.getLogger(__name__)

class SentimentFeatureBuilder:
    """
    Build features for meta-classifier stacking from multiple model outputs
    Focus on domain adaptation between FinBERT (financial) and general LLMs
    """
    
    @staticmethod
    def extract_model_features(model_result: Dict, model_type: str) -> Dict:
        """
        Extract standardized features from a single model result
        """
        features = {}
        
        # Raw scores
        numerical_score = model_result.get('numerical_score', 0.0)
        features[f'{model_type}_raw_score'] = numerical_score
        
        # Classification confidence (max probability or score certainty)
        detailed_scores = model_result.get('detailed_scores', {})
        
        if model_type == 'finbert':
            # FinBERT gives direct probabilities
            pos_score = detailed_scores.get('positive', 0.0)
            neg_score = detailed_scores.get('negative', 0.0)
            neu_score = detailed_scores.get('neutral', 0.0)
            
            # Normalize FinBERT scores to sum to 1.0 if needed
            values = np.clip([pos_score, neg_score, neu_score], 0.0, 1.0)
            s = sum(values) or 1.0
            pos_score, neg_score, neu_score = [v/s for v in values]
            
            max_prob = max(pos_score, neg_score, neu_score)
            features[f'{model_type}_confidence'] = max_prob
            features[f'{model_type}_pos_prob'] = pos_score
            features[f'{model_type}_neg_prob'] = neg_score
            features[f'{model_type}_neu_prob'] = neu_score
            
        else:  # LLM models (Gemini/OpenAI)
            # Convert to probabilities from overall score
            overall_score = detailed_scores.get('overall', 0.5)
            pos_score = detailed_scores.get('positive', 0.0)
            neg_score = detailed_scores.get('negative', 0.0)
            neu_score = detailed_scores.get('neutral', 0.0)
            
            # If individual scores not available, derive from overall
            if pos_score + neg_score + neu_score == 0:
                if overall_score > 0.6:
                    pos_score = overall_score * 0.8
                    neu_score = (1 - overall_score) * 0.7
                    neg_score = 1 - pos_score - neu_score
                elif overall_score < 0.4:
                    neg_score = (1 - overall_score) * 0.8
                    neu_score = overall_score * 0.7
                    pos_score = 1 - neg_score - neu_score
                else:
                    neu_score = 0.6
                    pos_score = (overall_score - 0.5) * 0.8 if overall_score > 0.5 else 0.1
                    neg_score = 1 - pos_score - neu_score
            
            # Clamp and normalize all derived scores to ensure valid probabilities
            values = np.clip([pos_score, neg_score, neu_score], 0.0, 1.0)
            s = sum(values) or 1.0
            pos_score, neg_score, neu_score = [v/s for v in values]
            
            max_prob = max(pos_score, neg_score, neu_score)
            features[f'{model_type}_confidence'] = max_prob
            features[f'{model_type}_pos_prob'] = pos_score
            features[f'{model_type}_neg_prob'] = neg_score
            features[f'{model_type}_neu_prob'] = neu_score
            features[f'{model_type}_overall'] = overall_score
        
        # Score magnitude (how far from neutral)
        features[f'{model_type}_magnitude'] = abs(numerical_score)
        
        # Classification as one-hot
        classification = model_result.get('classification', 'neutral')
        features[f'{model_type}_is_positive'] = 1 if classification == 'positive' else 0
        features[f'{model_type}_is_negative'] = 1 if classification == 'negative' else 0
        features[f'{model_type}_is_neutral'] = 1 if classification == 'neutral' else 0
        
        return features
    
    @staticmethod
    def extract_agreement_features(finbert_result: Dict, llm_result: Dict, 
                                 model_type: str) -> Dict:
        """
        Extract cross-model agreement and disagreement features with proper validation
        """
        features = {}
        
        # Score difference with NaN protection
        finbert_score = finbert_result.get('numerical_score', 0)
        llm_score = llm_result.get('numerical_score', 0)
        
        # Validate scores are valid numbers
        if np.isnan(finbert_score) or np.isinf(finbert_score):
            finbert_score = 0.0
        if np.isnan(llm_score) or np.isinf(llm_score):
            llm_score = 0.0
            
        score_diff = abs(finbert_score - llm_score)
        features['score_difference'] = score_diff
        features['score_difference_squared'] = score_diff ** 2
        
        # Classification agreement
        finbert_class = finbert_result.get('classification', 'neutral')
        llm_class = llm_result.get('classification', 'neutral')
        features['classifications_agree'] = 1 if finbert_class == llm_class else 0
        
        # Direction agreement
        finbert_direction = 1 if finbert_class == 'positive' else (-1 if finbert_class == 'negative' else 0)
        llm_direction = 1 if llm_class == 'positive' else (-1 if llm_class == 'negative' else 0)
        features['directions_agree'] = 1 if finbert_direction * llm_direction >= 0 else 0
        
        # Confidence calculation with proper validation
        finbert_detailed = finbert_result.get('detailed_scores', {})
        if finbert_detailed and len(finbert_detailed) > 0:
            try:
                valid_scores = [v for v in finbert_detailed.values() if isinstance(v, (int, float)) and not np.isnan(v)]
                finbert_conf = max(valid_scores) if valid_scores else 0.33
            except (ValueError, TypeError):
                finbert_conf = 0.33
        else:
            finbert_conf = 0.33
            
        llm_detailed = llm_result.get('detailed_scores', {})
        if llm_detailed and len(llm_detailed) > 0:
            try:
                llm_scores_list = [
                    llm_detailed.get('positive', 0.33),
                    llm_detailed.get('negative', 0.33), 
                    llm_detailed.get('neutral', 0.33)
                ]
                valid_llm_scores = [v for v in llm_scores_list if isinstance(v, (int, float)) and not np.isnan(v)]
                llm_conf = max(valid_llm_scores) if valid_llm_scores else 0.33
            except (ValueError, TypeError):
                llm_conf = 0.33
        else:
            llm_conf = 0.33
        
        features['finbert_confident'] = 1 if finbert_conf > 0.6 else 0
        features[f'{model_type}_confident'] = 1 if llm_conf > 0.6 else 0
        features['both_confident'] = features['finbert_confident'] * features[f'{model_type}_confident']
        features['neither_confident'] = (1 - features['finbert_confident']) * (1 - features[f'{model_type}_confident'])
        
        features['finbert_domain_advantage'] = features['finbert_confident']
        
        return features
    
    @staticmethod
    def extract_text_features(text: str, segment_count: int = 1) -> Dict:
        """
        Extract text-level features that might affect model performance
        """
        features = {}
        
        # Basic text statistics
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['segment_count'] = segment_count
        
        # Financial keywords (FinBERT should perform better on these)
        financial_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'market', 'stock', 'share',
            'dividend', 'growth', 'decline', 'bullish', 'bearish', 'volatility',
            'investment', 'return', 'yield', 'valuation', 'financial', 'fiscal',
            'quarter', 'annual', 'guidance', 'outlook', 'analyst', 'consensus',
            'eps', 'ebitda', 'margin', 'debt', 'equity', 'cash flow', 'balance sheet'
        ]
        
        text_lower = text.lower()
        financial_count = sum(1 for keyword in financial_keywords if keyword in text_lower)
        features['financial_keyword_count'] = financial_count
        features['financial_keyword_density'] = financial_count / max(len(text.split()), 1)
        features['is_financial_heavy'] = 1 if financial_count >= 3 else 0
        
        # Sentiment intensity words
        positive_words = ['strong', 'excellent', 'outstanding', 'beat', 'exceed', 'growth', 'up', 'rise', 'gain']
        negative_words = ['weak', 'poor', 'miss', 'decline', 'down', 'fall', 'loss', 'drop', 'concern']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        features['positive_word_count'] = pos_count
        features['negative_word_count'] = neg_count
        features['sentiment_word_ratio'] = pos_count / max(pos_count + neg_count, 1)
        
        return features
    
    @staticmethod
    def build_feature_matrix(finbert_results: List[Dict], 
                           llm_results: List[Dict],
                           texts: List[str],
                           model_type: str = 'gemini') -> np.ndarray:
        """
        Build complete feature matrix for stacking
        """
        all_features = []
        
        for i in range(len(finbert_results)):
            sample_features = {}
            
            # Extract features from each model
            finbert_features = SentimentFeatureBuilder.extract_model_features(
                finbert_results[i], 'finbert'
            )
            llm_features = SentimentFeatureBuilder.extract_model_features(
                llm_results[i], model_type
            )
            
            # Extract cross-model features
            agreement_features = SentimentFeatureBuilder.extract_agreement_features(
                finbert_results[i], llm_results[i], model_type
            )
            
            # Extract text features
            text_features = SentimentFeatureBuilder.extract_text_features(texts[i])
            
            # Combine all features
            sample_features.update(finbert_features)
            sample_features.update(llm_features)
            sample_features.update(agreement_features)
            sample_features.update(text_features)
            
            all_features.append(sample_features)
        
        # Convert to numpy array
        if not all_features:
            return np.array([])
        
        # Get consistent feature ordering
        feature_names = sorted(all_features[0].keys())
        feature_matrix = np.array([
            [sample[feature_name] for feature_name in feature_names]
            for sample in all_features
        ])
        
        return feature_matrix, feature_names
    
    @staticmethod
    def build_single_sample_features(finbert_result: Dict, 
                                   llm_result: Dict,
                                   text: str,
                                   model_type: str = 'gemini',
                                   feature_names: List[str] = None) -> np.ndarray:
        """
        Build features for a single sample (for prediction)
        """
        sample_features = {}
        
        # Extract all feature types
        finbert_features = SentimentFeatureBuilder.extract_model_features(
            finbert_result, 'finbert'
        )
        llm_features = SentimentFeatureBuilder.extract_model_features(
            llm_result, model_type
        )
        agreement_features = SentimentFeatureBuilder.extract_agreement_features(
            finbert_result, llm_result, model_type
        )
        text_features = SentimentFeatureBuilder.extract_text_features(text)
        
        # Combine all features
        sample_features.update(finbert_features)
        sample_features.update(llm_features)
        sample_features.update(agreement_features)
        sample_features.update(text_features)
        
        # If feature names provided, ensure consistent ordering
        if feature_names:
            feature_vector = np.array([
                sample_features.get(feature_name, 0.0) for feature_name in feature_names
            ])
        else:
            feature_names = sorted(sample_features.keys())
            feature_vector = np.array([
                sample_features[feature_name] for feature_name in feature_names
            ])
        
        return feature_vector.reshape(1, -1), feature_names
