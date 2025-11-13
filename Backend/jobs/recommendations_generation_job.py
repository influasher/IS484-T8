"""
Recommendations Generation Job
Generates fresh investment recommendations and portfolio health assessments for all clients.

This job is designed to run as a Kubernetes CronJob daily at 8 AM UTC.
It creates buy/sell recommendations based on updated portfolio and entity data.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.config import config
from app.models import db, User
from app.models.user import UserRole
from app.services.recommendation_service import get_client_recommendations
from app.services.portfolio_service import get_client_portfolio_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RecommendationsGenerationJob:
    """Job to generate recommendations for all clients"""

    def __init__(self, app: Flask):
        self.app = app
        self.max_recommendations_per_client = int(os.getenv('MAX_RECOMMENDATIONS_PER_CLIENT', '10'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.include_portfolio_health = os.getenv('INCLUDE_PORTFOLIO_HEALTH', 'true').lower() == 'true'
        self.generate_reports = os.getenv('GENERATE_REPORTS', 'false').lower() == 'true'

    def run(self):
        """Main job execution"""
        logger.info("Starting recommendations generation job")
        start_time = datetime.now()

        with self.app.app_context():
            try:
                # Get all clients
                clients = User.query.filter_by(role=UserRole.CLIENT).all()
                logger.info(f"Found {len(clients)} clients to process")

                success_count = 0
                error_count = 0
                total_recommendations = 0
                total_health_assessments = 0

                # Process clients in batches
                for i in range(0, len(clients), self.batch_size):
                    batch = clients[i:i + self.batch_size]
                    logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(clients) + self.batch_size - 1)//self.batch_size}")

                    for client in batch:
                        try:
                            logger.info(f"Processing client: {client.email}")

                            # Generate recommendations
                            recommendations = self._generate_client_recommendations(client)
                            total_recommendations += len(recommendations)

                            # Generate portfolio health assessment
                            health_data = None
                            if self.include_portfolio_health:
                                health_data = self._generate_portfolio_health(client)
                                if health_data and 'error' not in health_data:
                                    total_health_assessments += 1

                            # Optional: Store recommendations in database or send notifications
                            if self.generate_reports:
                                self._process_recommendations_output(client, recommendations, health_data)

                            success_count += 1
                            logger.info(f"✅ Generated {len(recommendations)} recommendations for {client.email}")

                        except Exception as e:
                            error_count += 1
                            logger.error(f"❌ Failed to generate recommendations for {client.email}: {e}")
                            continue

                # Summary
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"""
Recommendations generation job completed:
- Duration: {duration:.2f} seconds
- Total clients: {len(clients)}
- Successful: {success_count}
- Errors: {error_count}
- Total recommendations generated: {total_recommendations}
- Portfolio health assessments: {total_health_assessments}
- Average recommendations per client: {total_recommendations/max(success_count, 1):.1f}
- Success rate: {(success_count/len(clients)*100):.1f}%
                """)

                if error_count > 0:
                    logger.warning(f"Job completed with {error_count} errors")
                    if error_count > len(clients) * 0.5:  # More than 50% errors
                        sys.exit(1)
                else:
                    logger.info("Job completed successfully")

            except Exception as e:
                logger.error(f"Fatal error in recommendations generation job: {e}")
                sys.exit(1)

    def _generate_client_recommendations(self, client: User) -> List[Dict[str, Any]]:
        """Generate recommendations for a specific client"""
        try:
            recommendations = get_client_recommendations(
                str(client.id),
                limit=self.max_recommendations_per_client
            )

            logger.debug(f"Generated {len(recommendations)} recommendations for {client.email}")

            # Log recommendation summary
            if recommendations:
                buy_count = len([r for r in recommendations if r['action'] == 'BUY'])
                sell_count = len([r for r in recommendations if r['action'] == 'SELL'])
                logger.debug(f"  - {buy_count} BUY recommendations")
                logger.debug(f"  - {sell_count} SELL recommendations")

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations for {client.email}: {e}")
            return []

    def _generate_portfolio_health(self, client: User) -> Dict[str, Any]:
        """Generate portfolio health assessment for a specific client"""
        try:
            health_data = get_client_portfolio_health(str(client.id))

            if 'error' not in health_data:
                score = health_data.get('overall_health_score', 0)
                logger.debug(f"Portfolio health score for {client.email}: {score:.1f}/100")

                # Log key health metrics
                cash_analysis = health_data.get('cash_analysis', {})
                position_analysis = health_data.get('position_analysis', {})

                if cash_analysis.get('status') != 'healthy':
                    logger.debug(f"  - Cash position: {cash_analysis.get('status', 'unknown')}")

                if position_analysis.get('oversized_count', 0) > 0:
                    logger.debug(f"  - Oversized positions: {position_analysis['oversized_count']}")
            else:
                logger.warning(f"Portfolio health error for {client.email}: {health_data['error']}")

            return health_data

        except Exception as e:
            logger.error(f"Failed to generate portfolio health for {client.email}: {e}")
            return {'error': str(e)}

    def _process_recommendations_output(self, client: User, recommendations: List[Dict], health_data: Dict):
        """Process the generated recommendations and health data"""
        # This is where you could:
        # 1. Store recommendations in a separate table
        # 2. Send email notifications to RMs
        # 3. Generate PDF reports
        # 4. Update client dashboard data

        logger.debug(f"Processing output for {client.email}")

        # Example: Log high-priority recommendations
        high_priority_recs = [
            r for r in recommendations
            if r.get('recommendation_confidence', 0) > 0.8
        ]

        if high_priority_recs:
            logger.info(f"High-priority recommendations for {client.email}:")
            for rec in high_priority_recs[:3]:  # Log top 3
                logger.info(f"  - {rec['action']} {rec['entity_name']} ({rec['recommendation_confidence']:.0%} confidence)")

        # Example: Log health warnings
        if health_data and 'overall_health_score' in health_data:
            score = health_data['overall_health_score']
            if score < 70:
                logger.warning(f"Portfolio health concern for {client.email}: {score:.1f}/100")


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
    logger.info("Initializing recommendations generation job")

    try:
        app = create_app()
        job = RecommendationsGenerationJob(app)
        job.run()

    except Exception as e:
        logger.error(f"Failed to initialize recommendations generation job: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()