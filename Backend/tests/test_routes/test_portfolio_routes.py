import unittest
import uuid
from datetime import datetime, timezone, timedelta
from tests.test_routes.setup_mock_db import test_db
from app import db
from app.models.user import User
from app.models.entity import Entity
from app.models.client_portfolio import ClientPortfolio
from app.models.client_performance import ClientPerformance

class PortfolioIntegrationTest(unittest.TestCase):
    def _seed_test_data(self):
        """Seed DB with test clients, entities, portfolios, and performance history"""
        # Create test client
        self.client_user = User(
            id=uuid.uuid4(),
            username="client1",
            email="client1@example.com",
            first_name="Client",
            last_name="One",
            role="CLIENT"
        )
        db.session.add(self.client_user)

        # Create test entities
        self.entity1 = Entity(
            id=uuid.uuid4(),
            name="Alpha Corp",
            ticker="ALPHA",
            sentiment_score=0.5,
            classification="bullish",
            asset_type="stock",
            sector=["Technology"]
        )
        db.session.add(self.entity1)

        # Create test portfolio for client
        self.portfolio = ClientPortfolio(
            user_id=self.client_user.id,
            entity_id=self.entity1.id,
            qty=10,
            average_cost_basis=100,
            total_invested=1000,
            current_price=120,
            current_market_value=1200,
            unrealized_pnl=200,
            unrealized_pnl_percent=20,
            portfolio_allocation_percent=50
        )
        db.session.add(self.portfolio)

        # Create client performance history
        self.performance = ClientPerformance(
            client_uuid=self.client_user.id,
            datetime=datetime.now(timezone.utc) - timedelta(days=1),
            daily_performance=1.5
        )
        db.session.add(self.performance)

        db.session.commit()

    def test_get_client_portfolio_success(self):
        """Test retrieving portfolio allocations for a client"""
        with test_db() as client:
            self._seed_test_data()
            response = client.get(f"/api/portfolio/{self.client_user.id}")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["client_id"], str(self.client_user.id))
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["allocation"][0]["name"], "ALPHA")
            self.assertEqual(data["allocation"][0]["value"], 1200)

    def test_get_client_portfolio_not_found(self):
        """Test 404 if client does not exist"""
        with test_db() as client:
            self._seed_test_data()
            fake_id = uuid.uuid4()
            response = client.get(f"/api/portfolio/{fake_id}")
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertIn("Client not found", data["error"])

    def test_get_client_performance_success(self):
        """Test retrieving performance history"""
        with test_db() as client:
            self._seed_test_data()
            response = client.get(f"/api/portfolio/performance/{self.client_user.id}")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["client_id"], str(self.client_user.id))
            self.assertEqual(data["count"], 1)
            self.assertAlmostEqual(data["performance"][0]["value"], 1.5)

    def test_get_client_performance_not_found(self):
        """Test 404 when client performance is requested for non-existent client"""
        with test_db() as client:
            self._seed_test_data()
            fake_id = uuid.uuid4()
            response = client.get(f"/api/portfolio/performance/{fake_id}")
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertIn("Client not found", data["error"])

    def test_portfolio_calculations(self):
        """Integration test: verify portfolio P&L calculations"""
        with test_db() as client:
            self._seed_test_data()
            self.portfolio.calculate_current_values()
            self.portfolio.calculate_portfolio_allocation(total_portfolio_value=2400)
            self.assertEqual(self.portfolio.unrealized_pnl, 200)
            self.assertAlmostEqual(self.portfolio.unrealized_pnl_percent, 20)
            self.assertAlmostEqual(self.portfolio.portfolio_allocation_percent, 50)

