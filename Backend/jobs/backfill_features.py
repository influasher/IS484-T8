"""
Backfill missing features for user_feedback queue items
Run this once to fix existing data
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.config import config
from app.models import db
from app.models.active_learning import LabelingQueue
from app.models.news import News
from app.services.sentiment.features import SentimentFeatureBuilder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_features():
    """Backfill features for queue items with empty features_json"""
    app = Flask(__name__)
    env = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    db.init_app(app)
    
    with app.app_context():
        # Get ALL queue items, then filter in Python (simpler and more reliable)
        all_items = LabelingQueue.query.all()
        
        # Filter for items with empty/missing features
        empty_feature_items = [
            item for item in all_items 
            if item.features_json is None or 
               item.features_json == [] or 
               (isinstance(item.features_json, list) and len(item.features_json) == 0)
        ]
        
        logger.info(f"Found {len(empty_feature_items)} items with missing features out of {len(all_items)} total")
        
        if len(empty_feature_items) == 0:
            logger.info("✓ No items need backfilling")
            return
        
        feature_builder = SentimentFeatureBuilder()
        updated_count = 0
        
        for item in empty_feature_items:
            try:
                # Get associated news article if available
                if item.news_id:
                    news = News.query.filter_by(id=item.news_id).first()
                    if news:
                        # Use news data
                        finbert_score = news.finbert_score / 100.0
                        llm_score = news.second_model_score / 100.0
                        text = news.summary or news.title or news.content[:500]
                    else:
                        # Use queue item data
                        finbert_score = item.finbert_score / 100.0
                        llm_score = item.llm_score / 100.0
                        text = item.text
                else:
                    finbert_score = item.finbert_score / 100.0
                    llm_score = item.llm_score / 100.0
                    text = item.text
                
                # Reconstruct results
                finbert_result = {
                    'numerical_score': finbert_score,
                    'classification': 'positive' if finbert_score > 0.1 else ('negative' if finbert_score < -0.1 else 'neutral'),
                    'detailed_scores': {
                        'positive': max(0, finbert_score),
                        'negative': max(0, -finbert_score),
                        'neutral': 1.0 - abs(finbert_score)
                    }
                }
                
                llm_result = {
                    'numerical_score': llm_score,
                    'classification': 'positive' if llm_score > 0.1 else ('negative' if llm_score < -0.1 else 'neutral'),
                    'detailed_scores': {
                        'positive': max(0, llm_score),
                        'negative': max(0, -llm_score),
                        'neutral': 1.0 - abs(llm_score)
                    }
                }
                
                # Build features
                features, feature_names = feature_builder.build_single_sample_features(
                    finbert_result, llm_result, text, item.model_type or 'gemini'
                )
                
                # Update item
                item.features_json = features.tolist() if hasattr(features, 'tolist') else list(features[0])
                item.feature_names_json = list(feature_names)
                
                updated_count += 1
                
                if updated_count % 10 == 0:
                    logger.info(f"Updated {updated_count}/{len(empty_feature_items)} items...")
                    
            except Exception as e:
                logger.error(f"Error processing item {item.id}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"✓ Successfully backfilled features for {updated_count} items")


if __name__ == '__main__':
    backfill_features()
