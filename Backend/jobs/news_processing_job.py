"""
News Processing Job - Orchestrator for Service Pipeline

This job is designed to run as a Kubernetes CronJob every 1-2 days.
It orchestrates the existing service methods without reimplementing them.
It orchestrates the existing service methods without reimplementing them.

The job performs:
1. URL fetching from GNews API for all active entities
2. Delegates to get_article_details() which handles:
   - Article scraping using crawl4ai + newspaper
   - LLM-based entity extraction (companies, regions, sectors via news_interpreter)
   - Sentiment analysis using ensemble of FinBERT + Gemini
   - SHAP explainability generation
3. Uploads SHAP visualizations to Azure Blob Storage
4. Saves all data to News table with proper field population:
   - entities: [ticker symbols]
   - company_names: [extracted company names]
   - tags: [keywords from article]
   - All sentiment scores, confidence, agreement_rate
2. Delegates to get_article_details() which handles:
   - Article scraping using crawl4ai + newspaper
   - LLM-based entity extraction (companies, regions, sectors via news_interpreter)
   - Sentiment analysis using ensemble of FinBERT + Gemini
   - SHAP explainability generation
3. Uploads SHAP visualizations to Azure Blob Storage
4. Saves all data to News table with proper field population:
   - entities: [ticker symbols]
   - company_names: [extracted company names]
   - tags: [keywords from article]
   - All sentiment scores, confidence, agreement_rate
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.config import config
from app.models import db, News, Entity, SentimentHistory
from app.services.data_ingestion_gnews import get_premium_news_sources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NewsProcessor:
    """
    News Processing Pipeline - Orchestrator for Services

    This class delegates to service methods instead of reimplementing them.
    """


    def __init__(self, app: Flask):
        self.app = app

        
    def process_entity_news(self, entity: Entity, lookback_days: int = 2) -> Dict[str, Any]:
        """
        Process news for a single entity using the existing service.

        Delegates to get_premium_news_sources() which handles:
        - Fetching URLs from GNews
        - Scraping articles
        - Entity extraction
        - Sentiment analysis
        - Quality evaluation
        - Database insertion

        Args:
            entity: Entity object with ticker and name
            lookback_days: Number of days to look back for news

        Returns:
            Dict with processing metrics
        """
        logger.info(f"Processing news for entity: {entity.name} ({entity.ticker})")

        with self.app.app_context():
            try:
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=lookback_days)

                # Format dates as tuples (year, month, day) for GNews
                start_date_tuple = (start_date.year, start_date.month, start_date.day)
                end_date_tuple = (end_date.year, end_date.month, end_date.day)

                # Call the existing service which does everything
                query = entity.ticker or entity.name
                result = get_premium_news_sources(query, start_date_tuple, end_date_tuple)

                metrics = result.get('metrics', {})
                logger.info(
                    f"Entity {entity.ticker}: "
                    f"Fetched={metrics.get('total_articles_fetched', 0)}, "
                    f"Saved={metrics.get('successful_scrapes', 0)}, "
                    f"Failed={metrics.get('failed_scrapes', 0)}, "
                    f"LowQuality={metrics.get('low_quality_skipped', 0)}"
                )

                return metrics

            except Exception as e:
                logger.error(f"Error processing entity {entity.ticker}: {str(e)}", exc_info=True)
                return {
                    'total_articles_fetched': 0,
                    'successful_scrapes': 0,
                    'failed_scrapes': 1,
                    'low_quality_skipped': 0
                }

    def update_sentiment_history(self, news_articles: List[News]):
        """
        Update SentimentHistory table with entity-level aggregated sentiment
        
        Args:
            news_articles: List of processed News articles
        """
        with self.app.app_context():
            try:
                logger.info("Updating SentimentHistory with aggregated sentiment")
                
                # Group articles by entity
                from collections import defaultdict
                entity_articles = defaultdict(list)
                
                for article in news_articles:
                    # Map company names to entity IDs
                    for company_name in article.company_names or []:
                        entity = Entity.query.filter_by(name=company_name).first()
                        if entity:
                            entity_articles[entity.id].append(article)
                
                # Calculate aggregated sentiment for each entity
                for entity_id, articles in entity_articles.items():
                    if not articles:
                        continue
                    
                    # Weighted average of sentiment scores
                    total_weight = sum(a.confidence or 1.0 for a in articles)
                    weighted_score = sum(
                        (a.score or 0.0) * (a.confidence or 1.0) 
                        for a in articles
                    ) / total_weight if total_weight > 0 else 0.0
                    
                    # Determine overall sentiment
                    if weighted_score > 0.2:
                        overall_sentiment = 'positive'
                    elif weighted_score < -0.2:
                        overall_sentiment = 'negative'
                    else:
                        overall_sentiment = 'neutral'
                    
                    # Create SentimentHistory entry
                    sentiment_history = SentimentHistory(
                        entity_id=entity_id,
                        date=datetime.utcnow().date(),
                        sentiment=overall_sentiment,
                        score=weighted_score,
                        article_count=len(articles),
                        confidence=sum(a.confidence or 0.0 for a in articles) / len(articles)
                    )
                    
                    db.session.add(sentiment_history)
                
                db.session.commit()
                logger.info(f"Updated SentimentHistory for {len(entity_articles)} entities")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating sentiment history: {str(e)}")
    
    def run(self, lookback_days: int = 2, max_entities: Optional[int] = None):
        """
        Run the full news processing pipeline

        Args:
            lookback_days: Number of days to look back for news
            max_entities: Maximum number of entities to process (None = all)
        """
        logger.info("=" * 80)
        logger.info("Starting News Processing Job")
        logger.info(f"Lookback days: {lookback_days}")
        logger.info(f"Max entities: {max_entities or 'all'}")
        logger.info("=" * 80)

        start_time = datetime.utcnow()


        try:
            with self.app.app_context():
                # Get all active entities
                entities = Entity.query.filter(
                    Entity.ticker.isnot(None),
                    Entity.ticker != ''
                ).all()

                if not entities:
                    logger.warning("No entities found in database")
                    return

                logger.info(f"Found {len(entities)} entities to process")

                # Limit if specified
                if max_entities:
                    entities = entities[:max_entities]
                    logger.info(f"Limited to {len(entities)} entities")

                # Aggregate metrics
                total_metrics = {
                    'total_articles_fetched': 0,
                    'successful_scrapes': 0,
                    'failed_scrapes': 0,
                    'low_quality_skipped': 0,
                    'duplicates_skipped': 0,
                    'paywall_flagged': 0
                }

                # Process each entity
                for i, entity in enumerate(entities, 1):
                    logger.info(f"Processing entity {i}/{len(entities)}: {entity.name} ({entity.ticker})")

                    metrics = self.process_entity_news(entity, lookback_days)

                    # Aggregate metrics
                    for key in total_metrics:
                        total_metrics[key] += metrics.get(key, 0)

                    # Small delay between entities to be respectful to GNews API
                    time.sleep(2)

                # Get newly added articles for sentiment history update
                cutoff_time = start_time
                recent_articles = News.query.filter(
                    News.scraped_at >= cutoff_time
                ).all()

                # Update sentiment history with aggregated data
                if recent_articles:
                    logger.info(f"Updating sentiment history for {len(recent_articles)} new articles")
                    self.update_sentiment_history(recent_articles)

                # Summary
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()

                logger.info("=" * 80)
                logger.info("News Processing Job Completed")
                logger.info(f"Entities processed: {len(entities)}")
                logger.info(f"Articles fetched: {total_metrics['total_articles_fetched']}")
                logger.info(f"Articles saved: {total_metrics['successful_scrapes']}")
                logger.info(f"Failed: {total_metrics['failed_scrapes']}")
                logger.info(f"Low quality skipped: {total_metrics['low_quality_skipped']}")
                logger.info(f"Duration: {duration:.2f} seconds")
                logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Fatal error in news processing job: {str(e)}", exc_info=True)
            raise


def create_app():
    """Create Flask app for job context"""
    app = Flask(__name__)
    
    # Load configuration
    env = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    # Initialize database
    db.init_app(app)
    
    return app


def main():
    """Main entry point for the job"""
    # Get configuration from environment
    lookback_days = int(os.getenv('LOOKBACK_DAYS', '2'))
    max_entities = os.getenv('MAX_ENTITIES')
    max_entities = int(max_entities) if max_entities else None

    # Create app and processor
    app = create_app()
    processor = NewsProcessor(app)

    # Run the pipeline
    processor.run(lookback_days=lookback_days, max_entities=max_entities)


if __name__ == '__main__':
    main()
