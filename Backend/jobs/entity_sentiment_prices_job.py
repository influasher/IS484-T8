"""
Entity Sentiment Job
Updates sentiment scores for all tracked entities based on recent news.

This job is designed to run as a Kubernetes CronJob daily at 7 AM UTC.
It refreshes sentiment analysis from recent news (last 7 days).
Note: Price updates are handled by the portfolio refresh job.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.config import config
from app.models import db, Entity
from app.services.entity_sentiment_aggregator import EntitySentimentAggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EntitySentimentJob:
    """Job to update entity sentiment data"""

    def __init__(self, app: Flask):
        self.app = app
        self.batch_size = int(os.getenv('BATCH_SIZE', '20'))
        self.sentiment_lookback_days = int(os.getenv('SENTIMENT_LOOKBACK_DAYS', '7'))

        # Initialize sentiment aggregator
        self.sentiment_aggregator = EntitySentimentAggregator(lookback_days=self.sentiment_lookback_days)

    def run(self):
        """Main job execution"""
        logger.info("Starting entity sentiment job")
        start_time = datetime.now()

        with self.app.app_context():
            try:
                # Get all entities with tickers
                entities = Entity.query.filter(Entity.ticker.isnot(None)).all()
                logger.info("Found %d entities to process", len(entities))
                logger.info("Sentiment lookback period: %d days", self.sentiment_lookback_days)

                success_count = 0
                error_count = 0
                sentiment_update_count = 0

                # Process entities in batches
                for i in range(0, len(entities), self.batch_size):
                    batch = entities[i:i + self.batch_size]
                    batch_num = i//self.batch_size + 1
                    total_batches = (len(entities) + self.batch_size - 1)//self.batch_size
                    logger.info("Processing batch %d/%d", batch_num, total_batches)

                    for entity in batch:
                        try:
                            logger.debug("Processing entity: %s (%s)", entity.name, entity.ticker)

                            # Update sentiment from recent news
                            sentiment_updated = False
                            try:
                                sentiment_result = self.sentiment_aggregator.update_entity_sentiment(entity.name)

                                if sentiment_result['success']:
                                    sentiment_updated = True
                                    sentiment_update_count += 1
                                    sentiment_data = sentiment_result['sentiment']

                                    logger.info(
                                        "Updated sentiment for %s: %s (%.2f) from %d articles",
                                        entity.name,
                                        sentiment_data['classification'],
                                        sentiment_data['sentiment_score'],
                                        sentiment_data['article_count']
                                    )
                                else:
                                    logger.debug("No sentiment update for %s: %s",
                                               entity.name, sentiment_result.get('error', 'Unknown error'))

                            except Exception as sentiment_error:
                                logger.warning("Failed to update sentiment for %s: %s", entity.name, sentiment_error)

                            if sentiment_updated:
                                success_count += 1
                                logger.debug("✅ Successfully updated sentiment for %s", entity.name)
                            else:
                                logger.debug("⚠️  No sentiment update for %s", entity.name)

                        except Exception as e:
                            error_count += 1
                            logger.error("❌ Failed to process entity %s: %s", entity.name, e)
                            continue

                    # Commit batch changes
                    try:
                        db.session.commit()
                        logger.info("Committed batch %d", batch_num)
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        logger.error("Failed to commit batch %d: %s", batch_num, e)

                # Summary
                duration = (datetime.now() - start_time).total_seconds()
                success_rate = (success_count/len(entities)*100) if entities else 0
                logger.info(
                    "Entity sentiment job completed:\n"
                    "- Duration: %.2f seconds\n"
                    "- Total entities: %d\n"
                    "- Sentiment updates: %d\n"
                    "- Successful processes: %d\n"
                    "- Errors: %d\n"
                    "- Success rate: %.1f%%\n"
                    "- Sentiment lookback: %d days",
                    duration, len(entities), sentiment_update_count,
                    success_count, error_count, success_rate, self.sentiment_lookback_days
                )

                if error_count > len(entities) * 0.5:  # More than 50% errors
                    logger.error("Job failed with too many errors: %d/%d", error_count, len(entities))
                    sys.exit(1)
                else:
                    logger.info("Job completed successfully")

            except Exception as e:
                logger.error("Fatal error in entity sentiment job: %s", e)
                sys.exit(1)


def create_app():
    """Create Flask application"""
    flask_env = os.getenv('FLASK_ENV', 'production')
    app = Flask(__name__)
    app.config.from_object(config[flask_env])

    # Initialize database
    db.init_app(app)

    return app


def main():
    """Main entry point"""
    logger.info("Initializing entity sentiment job")

    try:
        app = create_app()
        job = EntitySentimentJob(app)
        job.run()

    except Exception as e:
        logger.error("Failed to initialize entity sentiment job: %s", e)
        sys.exit(1)


if __name__ == '__main__':
    main()