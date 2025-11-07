import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SamplingStrategy(Enum):
    DISAGREEMENT = "disagreement"
    UNCERTAINTY = "uncertainty"  
    NEAR_NEUTRAL = "near_neutral"
    FINANCIAL_HEAVY = "financial_heavy"

@dataclass
class ActiveLearningSample:
    """
    Container for samples selected for active learning
    """
    text: str
    news_id: Optional[int]
    finbert_result: Dict
    llm_result: Dict
    model_type: str
    features: np.ndarray
    feature_names: List[str]
    disagreement_score: float
    uncertainty_score: float
    sampling_reason: str
    priority: int  # 1=highest, 5=lowest
    
class ActiveLearningSelector:
    """
    Select samples for human labeling based on model disagreement and uncertainty
    """
    
    def __init__(self, 
                 disagreement_threshold: float = 0.4,
                 uncertainty_threshold: float = 0.3,
                 near_neutral_threshold: float = 0.2):
        self.disagreement_threshold = disagreement_threshold
        self.uncertainty_threshold = uncertainty_threshold  
        self.near_neutral_threshold = near_neutral_threshold
        
    def calculate_disagreement_score(self, finbert_result: Dict, 
                                   llm_result: Dict) -> float:
        """
        Calculate disagreement score between models (0=agree, 1=maximum disagreement)
        """
        # Score difference component
        finbert_score = finbert_result.get('numerical_score', 0)
        llm_score = llm_result.get('numerical_score', 0)
        
        # Validate scores
        finbert_score = 0.0 if np.isnan(finbert_score) or np.isinf(finbert_score) else finbert_score
        llm_score = 0.0 if np.isnan(llm_score) or np.isinf(llm_score) else llm_score
        
        score_diff = abs(finbert_score - llm_score)
        score_disagreement = min(score_diff / 2.0, 1.0)  # Normalize to [0,1]
        
        # Classification disagreement
        finbert_class = finbert_result.get('classification', 'neutral')
        llm_class = llm_result.get('classification', 'neutral')
        class_disagreement = 0.0 if finbert_class == llm_class else 1.0
        
        # Opposite directions are especially problematic
        finbert_dir = 1 if finbert_class == 'positive' else (-1 if finbert_class == 'negative' else 0)
        llm_dir = 1 if llm_class == 'positive' else (-1 if llm_class == 'negative' else 0)
        
        opposite_directions = 1.0 if (finbert_dir * llm_dir < 0) else 0.0
        
        # Weighted combination
        disagreement = (0.4 * score_disagreement + 
                       0.3 * class_disagreement + 
                       0.3 * opposite_directions)
        
        return min(disagreement, 1.0)
    
    def calculate_uncertainty_score(self, finbert_result: Dict, 
                                  llm_result: Dict) -> float:
        """
        Calculate overall uncertainty score (0=confident, 1=very uncertain)
        """
        # FinBERT confidence with validation
        finbert_scores = finbert_result.get('detailed_scores', {})
        if finbert_scores:
            try:
                valid_scores = [v for v in finbert_scores.values() 
                              if isinstance(v, (int, float)) and not np.isnan(v)]
                finbert_max_prob = max(valid_scores) if valid_scores else 0.33
            except (ValueError, TypeError):
                finbert_max_prob = 0.33
        else:
            finbert_max_prob = 0.33
        
        finbert_uncertainty = 1.0 - finbert_max_prob
        
        # LLM confidence with validation
        llm_scores = llm_result.get('detailed_scores', {})
        llm_probs = [
            llm_scores.get('positive', 0.33),
            llm_scores.get('negative', 0.33), 
            llm_scores.get('neutral', 0.33)
        ]
        
        try:
            valid_llm_probs = [v for v in llm_probs if isinstance(v, (int, float)) and not np.isnan(v)]
            llm_max_prob = max(valid_llm_probs) if valid_llm_probs else 0.33
        except (ValueError, TypeError):
            llm_max_prob = 0.33
            
        llm_uncertainty = 1.0 - llm_max_prob
        
        # Average uncertainty
        avg_uncertainty = (finbert_uncertainty + llm_uncertainty) / 2.0
        
        return avg_uncertainty
    
    def calculate_near_neutral_score(self, finbert_result: Dict,
                                   llm_result: Dict) -> float:
        """
        Calculate how close predictions are to neutral boundary
        """
        finbert_score = finbert_result.get('numerical_score', 0)
        llm_score = llm_result.get('numerical_score', 0)
        
        # Validate scores
        finbert_score = 0.0 if np.isnan(finbert_score) or np.isinf(finbert_score) else finbert_score
        llm_score = 0.0 if np.isnan(llm_score) or np.isinf(llm_score) else llm_score
        
        finbert_score = abs(finbert_score)
        llm_score = abs(llm_score)
        
        # Score how close to neutral (0) each model is
        finbert_neutrality = 1.0 - min(finbert_score, 1.0)  # Higher = more neutral
        llm_neutrality = 1.0 - min(llm_score, 1.0)
        
        return (finbert_neutrality + llm_neutrality) / 2.0
    
    def should_sample_for_disagreement(self, disagreement_score: float,
                                     uncertainty_score: float,
                                     features_dict: Dict) -> Tuple[bool, str, int]:
        """
        Determine if sample should be selected for disagreement-based learning
        Returns: (should_sample, reason, priority)
        """
        # High disagreement cases
        if disagreement_score >= 0.8:
            return True, "High model disagreement", 1
            
        # Medium disagreement + high uncertainty
        if disagreement_score >= 0.6 and uncertainty_score >= 0.4:
            return True, "Medium disagreement + uncertainty", 2
            
        # Financial content with disagreement (FinBERT should be better)
        if (disagreement_score >= self.disagreement_threshold and 
            features_dict.get('is_financial_heavy', 0)):
            return True, "Financial content disagreement", 2
            
        # Confident disagreement (both models sure but different)
        if (disagreement_score >= 0.6 and uncertainty_score <= 0.3):
            return True, "Confident disagreement", 3
            
        return False, "", 5
    
    def should_sample_for_uncertainty(self, uncertainty_score: float,
                                    near_neutral_score: float,
                                    features_dict: Dict) -> Tuple[bool, str, int]:
        """
        Determine if sample should be selected for uncertainty-based learning
        """
        # Very high uncertainty
        if uncertainty_score >= 0.7:
            return True, "High uncertainty", 3
            
        # Near boundary cases that are uncertain
        if near_neutral_score >= 0.6 and uncertainty_score >= 0.5:
            return True, "Near-neutral uncertainty", 4
            
        # Financial content with uncertainty (domain expertise needed)
        if (uncertainty_score >= self.uncertainty_threshold and 
            features_dict.get('is_financial_heavy', 0)):
            return True, "Financial content uncertainty", 4
            
        return False, "", 5
    
    def select_samples(self, analysis_results: List[Dict],
                      texts: List[str],
                      news_ids: List[Optional[int]] = None,
                      max_samples: int = 10) -> List[ActiveLearningSample]:
        """
        Select samples for active learning from analysis results
        """
        if news_ids is None:
            news_ids = [None] * len(analysis_results)
            
        candidates = []
        
        for i, result in enumerate(analysis_results):
            if i >= len(texts):
                continue
                
            text = texts[i]
            news_id = news_ids[i] if i < len(news_ids) else None
            
            # Extract model results from integrated results
            segment_results = result.get('segment_results', [])
            if not segment_results:
                continue
                
            # Use first segment for simplicity (could aggregate)
            first_segment = segment_results[0]
            
            # Reconstruct individual model results
            finbert_score = first_segment.get('model_scores', {}).get('finbert', 0)
            llm_score = first_segment.get('model_scores', {}).get('second_model', 0)
            
            finbert_result = {
                'numerical_score': finbert_score,
                'classification': 'positive' if finbert_score > 0.1 else ('negative' if finbert_score < -0.1 else 'neutral'),
                'detailed_scores': {}  # Would need to reconstruct from features
            }
            
            llm_result = {
                'numerical_score': llm_score,  
                'classification': 'positive' if llm_score > 0.1 else ('negative' if llm_score < -0.1 else 'neutral'),
                'detailed_scores': {}
            }
            
            # Calculate scores
            disagreement_score = self.calculate_disagreement_score(finbert_result, llm_result)
            uncertainty_score = self.calculate_uncertainty_score(finbert_result, llm_result)
            near_neutral_score = self.calculate_near_neutral_score(finbert_result, llm_result)
            
            # Get features
            features = np.array(first_segment.get('features', []))
            feature_names = first_segment.get('feature_names', [])
            features_dict = dict(zip(feature_names, features)) if len(feature_names) == len(features) else {}
            
            # Check sampling criteria
            should_sample = False
            reason = ""
            priority = 5
            
            # Check disagreement-based sampling
            sample_disagree, reason_disagree, priority_disagree = self.should_sample_for_disagreement(
                disagreement_score, uncertainty_score, features_dict
            )
            
            if sample_disagree:
                should_sample = True
                reason = reason_disagree
                priority = priority_disagree
            
            # Check uncertainty-based sampling (lower priority)
            if not should_sample:
                sample_uncertain, reason_uncertain, priority_uncertain = self.should_sample_for_uncertainty(
                    uncertainty_score, near_neutral_score, features_dict
                )
                
                if sample_uncertain:
                    should_sample = True
                    reason = reason_uncertain  
                    priority = priority_uncertain
            
            if should_sample:
                sample = ActiveLearningSample(
                    text=text,
                    news_id=news_id,
                    finbert_result=finbert_result,
                    llm_result=llm_result,
                    model_type=result.get('model_type_used', 'gemini'),
                    features=features,
                    feature_names=feature_names,
                    disagreement_score=disagreement_score,
                    uncertainty_score=uncertainty_score,
                    sampling_reason=reason,
                    priority=priority
                )
                candidates.append(sample)
        
        # Sort by priority (1=highest) then by disagreement score
        candidates.sort(key=lambda x: (x.priority, -x.disagreement_score))
        
        # Return top candidates
        return candidates[:max_samples]
    
    def create_queue_items(self, samples: List[ActiveLearningSample]) -> List[Dict]:
        """
        Convert samples to queue items for database insertion - matches API schema
        """
        queue_items = []
        
        for sample in samples:
            queue_item = {
                'news_id': sample.news_id,
                'text': sample.text,
                'finbert_score': sample.finbert_result['numerical_score'],
                'llm_score': sample.llm_result['numerical_score'], 
                'model_type': sample.model_type,
                'disagreement_score': sample.disagreement_score,
                'uncertainty_score': sample.uncertainty_score,
                'sampling_reason': sample.sampling_reason,
                'priority': sample.priority,
                'features_json': sample.features.tolist(),  
                'feature_names_json': sample.feature_names  
            }
            queue_items.append(queue_item)
            
        return queue_items

# Usage functions for integration
def identify_disagreement_samples(sentiment_results: List[Dict], 
                                texts: List[str],
                                news_ids: List[Optional[int]] = None,
                                max_samples: int = 10) -> List[ActiveLearningSample]:
    """
    Convenience function to identify samples needing human labels
    """
    selector = ActiveLearningSelector(
        disagreement_threshold=0.5,  # Lower threshold to catch more cases
        uncertainty_threshold=0.4,
        near_neutral_threshold=0.3
    )
    
    return selector.select_samples(sentiment_results, texts, news_ids, max_samples)

def should_request_human_feedback(finbert_result: Dict, llm_result: Dict, 
                                text: str, features_dict: Dict = None) -> bool:
    """
    Quick check if a single analysis should trigger human feedback request
    Uses rich features from integration if available
    """
    selector = ActiveLearningSelector()
    
    # Use pre-calculated features if available
    if features_dict:
        disagreement = features_dict.get('score_difference', 
                                       selector.calculate_disagreement_score(finbert_result, llm_result))
        
        # Calculate uncertainty from confidence features
        finbert_conf = features_dict.get('finbert_confidence', 0.33)
        # Try to get LLM confidence (could be gemini_confidence or openai_confidence)
        llm_conf = features_dict.get('gemini_confidence', 
                                    features_dict.get('openai_confidence', 0.33))
        
        uncertainty = 1.0 - ((finbert_conf + llm_conf) / 2.0)
    else:
        disagreement = selector.calculate_disagreement_score(finbert_result, llm_result)
        uncertainty = selector.calculate_uncertainty_score(finbert_result, llm_result)
    
    features_dict = features_dict or {}
    
    # Log the inputs for diagnostics
    logger.info(
        "should_request_human_feedback: disagreement=%.4f uncertainty=%.4f finbert_num=%s llm_num=%s is_financial_heavy=%s",
        disagreement,
        uncertainty,
        finbert_result.get('numerical_score'),
        llm_result.get('numerical_score'),
        features_dict.get('is_financial_heavy', 'N/A')
    )
    
    should_sample, reason, priority = selector.should_sample_for_disagreement(
        disagreement, uncertainty, features_dict
    )
    
    logger.info("should_request_human_feedback decision: should_sample=%s reason=%s priority=%s", 
               should_sample, reason, priority)
    return should_sample
