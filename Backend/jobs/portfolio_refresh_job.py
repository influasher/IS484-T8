"""
Portfolio Refresh Job
Refreshes portfolio prices and recalculates portfolios for all clients.

This job is designed to run as a Kubernetes CronJob daily at 6 AM UTC.
It updates current market prices for all positions and recalculates portfolio metrics.
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.config import config
from app.models import db, User
from app.models.user import UserRole
from app.services.portfolio_service import PortfolioCalculationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PortfolioRefreshJob:
    """Job to refresh portfolios for all clients"""

    def __init__(self, app: Flask):
        self.app = app
        self.portfolio_service = PortfolioCalculationService()

    def run(self):
        """Main job execution"""
        logger.info("Starting portfolio refresh job")
        start_time = datetime.now()

        with self.app.app_context():
            try:
                # Get all clients
                clients = User.query.filter_by(role=UserRole.CLIENT).all()
                logger.info("Found %d clients to process", len(clients))

                success_count = 0
                error_count = 0

                for client in clients:
                    try:
                        logger.info(f"Processing client: {client.email}")

                        # Refresh prices for client's positions
                        price_result = self.portfolio_service.refresh_portfolio_prices(
                            str(client.id)
                        )
                        logger.info(
                            "Updated prices for %d/%d positions",
                            price_result['positions_updated'],
                            price_result['total_positions']
                        )

                        # Recalculate portfolio from transactions
                        portfolio_result = self.portfolio_service.calculate_portfolio_from_transactions(
                            str(client.id)
                        )
                        logger.info(
                            "Recalculated portfolio: $%.2f total value",
                            portfolio_result['total_portfolio_value']
                        )

                        success_count += 1
                        logger.info("✅ Successfully refreshed portfolio for %s", client.email)

                    except Exception as e:
                        error_count += 1
                        logger.error("❌ Failed to refresh portfolio for %s: %s", client.email, e)
                        continue

                # Summary
                duration = (datetime.now() - start_time).total_seconds()
                success_rate = (success_count/len(clients)*100) if clients else 0
                logger.info(
                    "Portfolio refresh job completed:\n"
                    "- Duration: %.2f seconds\n"
                    "- Total clients: %d\n"
                    "- Successful: %d\n"
                    "- Errors: %d\n"
                    "- Success rate: %.1f%%",
                    duration, len(clients), success_count, error_count, success_rate
                )

                if error_count > 0:
                    logger.warning("Job completed with %d errors", error_count)
                    sys.exit(1)
                else:
                    logger.info("Job completed successfully")

            except Exception as e:
                logger.error("Fatal error in portfolio refresh job: %s", e)
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
    logger.info("Initializing portfolio refresh job")

    try:
        app = create_app()
        job = PortfolioRefreshJob(app)
        job.run()

    except Exception as e:
        logger.error("Failed to initialize portfolio refresh job: %s", e)
        sys.exit(1)


if __name__ == '__main__':
    main()