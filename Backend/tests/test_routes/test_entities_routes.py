import unittest
from unittest.mock import patch
from app.models import Entity, User
from app import db
from tests.test_routes.setup_mock_db import test_db
import uuid
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

class EntityIntegrationTest(unittest.TestCase):
    def _create_sample_entities(self):
        """Helper to seed test DB with sample entities."""
        entities = [
            Entity(
                id=uuid.uuid4(),
                name="Alpha Corp",
                ticker="ALPHA",
                sentiment_score=0.7,
                classification="bullish",
                asset_type="stock",
                sector=["Technology"],
            ),
            Entity(
                id=uuid.uuid4(),
                name="Beta LLC",
                ticker="BETA",
                sentiment_score=-0.3,
                classification="bearish",
                asset_type="bond",
                sector=["Finance"],
            ),
            Entity(
                id=uuid.uuid4(),
                name="Gamma Inc",
                ticker="GAMMA",
                sentiment_score=0.1,
                classification="neutral",
                asset_type="etf",
                sector=["Energy"],
            ),
        ]

        rm = User(
                id=uuid.uuid4(),           
                username="tom123",          # must not be None
                email="tom@example.com",
                first_name="Tom",
                last_name="Tim",
                role="RELATIONSHIP_MANAGER",                  
                rm_id=None                    
            )
        db.session.add_all(entities)
        db.session.add(rm)
        db.session.commit()

        # Generate a valid JWT token
        self.access_token = create_access_token(identity=str(rm.id))
        self.entity_id = entities[0].id
        return entities[0]

    # Test cases for GET /api/entities/

    def test_get_entities_success(self):
        with test_db() as client:
            self._create_sample_entities()
            response = client.get("/api/entities/?page=1&per_page=2")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            self.assertIn("Entities fetched successfully", data["message"])
            self.assertLessEqual(len(data["data"]["entities"]), 2)

    def test_get_entities_search(self):
        with test_db() as client:
            self._create_sample_entities()
            response = client.get("/api/entities/?search=Beta")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            names = [entity["name"] for entity in data["data"]["entities"]]
            self.assertIn("Beta LLC", names)

    def test_get_entities_sort_desc(self):
        with test_db() as client:
            self._create_sample_entities()
            response = client.get("/api/entities/?sort_order=name-desc")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            names = [entity["name"] for entity in data["data"]["entities"]]
            self.assertEqual(names, sorted(names, reverse=True))

    def test_get_entities_not_found(self):
        with test_db() as client:
            self._create_sample_entities()
            response = client.get("/api/entities/?search=ZZZZZZ")
            self.assertEqual(response.status_code, 404)

            data = response.get_json()
            self.assertEqual(data["data"], [])
            self.assertIn("Entities not found", data["message"])

    # Test cases for GET /api/entities/get_all_tickers

    def test_get_all_tickers_success(self):
        """✅ Should return all tickers when entities exist."""
        with test_db() as client:
            self._create_sample_entities()

            response = client.get("/api/entities/get_all_tickers")
            data = response.get_json()

            assert response.status_code == 200
            assert data["message"] == "Tickers fetched successfully"
            assert isinstance(data["data"], list)

            # Extract tickers from response
            tickers = [item["ticker"] for item in data["data"]]
            assert set(tickers) == {"ALPHA", "BETA", "GAMMA"}

    def test_get_all_tickers_empty(self):
        """✅ Should return 404 when no entities exist."""
        with test_db() as client:
            response = client.get("/api/entities/get_all_tickers")
            data = response.get_json()

            assert response.status_code == 404
            assert data["message"] == "Tickers not found"
            assert data["data"] == []

    # Test cases for POST /api/entities/

    def test_create_entity_success(self):
        # Data for creating entity
        with test_db() as client:
            self._create_sample_entities()

            payload = {
                "name": "Theta Corp",
                "ticker": "THETA"
            }

            # Call POST /entities/
            response = client.post(
                "/api/entities/",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            self.assertEqual(response.status_code, 201)
            data = response.get_json()["data"]
            self.assertEqual(data["name"], payload["name"])
            self.assertEqual(data["ticker"], payload["ticker"])
            self.assertIsNone(data.get("summary"))

    def test_create_entity_missing_name(self):
        with test_db() as client:
            self._create_sample_entities()

            payload = {
                "ticker": "THETA"
            }

            with self.assertRaises(IntegrityError):
                client.post(
                    "/api/entities/",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
    
    # Test cases for PUT /api/entities/<entity_id>
        
    def test_update_entity_success(self):
        """✅ Should update entity fields successfully"""
        with test_db() as client:
            self._create_sample_entities()

            payload = {
                "sentiment_score": 0.9,
                "finbert_score": 0.8,
                "gemini_score": 0.7,
                "open_ai_score": 0.6,
                "confidence_score": 0.95,
                "time_decay": 0.1,
                "simple_average": 0.8,
                "classification": "very bullish"
            }

            response = client.put(
                f"/api/entities/{self.entity_id}",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            self.assertEqual(response.status_code, 200)
            data = response.get_json()["data"]

            for key, value in payload.items():
                self.assertEqual(data[key], value)

    def test_update_entity_not_found(self):
        """❌ Should return 404 when entity does not exist"""
        with test_db() as client:
            self._create_sample_entities()
            fake_id = uuid.uuid4()

            payload = {"sentiment_score": 0.5}

            response = client.put(
                f"/api/entities/{fake_id}",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertEqual(data["message"], "Entity not found")

    # Test cases for GET /api/entities/<ticker>

    def test_get_entity_details_success(self):
        """✅ Should return entity details for a valid ticker"""
        with test_db() as client:
            entity1 = self._create_sample_entities()

            response = client.get(f"/api/entities/{entity1.ticker}")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            self.assertEqual(data["data"]["ticker"], entity1.ticker)
            self.assertEqual(data["data"]["name"], entity1.name)
            self.assertIn("sentiment_score", data["data"])
            self.assertIn("classification", data["data"])
            self.assertEqual(data["message"], "Entity fetched successfully")

    def test_get_entity_details_not_found(self):
        """❌ Should return 404 when ticker does not exist"""
        with test_db() as client:
            self._create_sample_entities()

            response = client.get("/api/entities/UNKNOWN")
            self.assertEqual(response.status_code, 404)

            data = response.get_json()
            self.assertEqual(data["data"], None)
            self.assertEqual(data["message"], "Entity not found")

    # Test cases for GET /api/entities/<uuid>/stock
    
    @patch("app.routes.entities.get_stock_price")
    def test_get_entity_stock_price(self, mock_get_stock_price):
        """✅ Test /<uuid>/stock endpoint with mocked stock price"""
        mock_get_stock_price.return_value = 123.45

        with test_db() as client:
            entity = self._create_sample_entities()
            response = client.get(f"/api/entities/{entity.id}/stock")
            
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["name"], entity.name)
            self.assertEqual(data["data"]["stock_price"], 123.45)
            self.assertEqual(data["message"], "Stock price fetched successfully")

    # Test cases for GET /api/entities/<uuid>/chart

    @patch("app.routes.entities.get_stock_history")
    def test_get_entity_stock_chart_default_period(self, mock_get_stock_history):
        """✅ Test /<uuid>/chart endpoint with default period"""
        mock_get_stock_history.return_value = {
            "dates": ["2025-01-01", "2025-01-02"],
            "prices": [100, 101],
            "performance": 1.0,
        }

        with test_db() as client:
            entity = self._create_sample_entities()
            response = client.get(f"/api/entities/{entity.id}/chart")
            
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["name"], entity.name)
            self.assertEqual(data["data"]["ticker"], entity.ticker)
            self.assertEqual(data["data"]["period"], "1Y")  # default
            self.assertEqual(data["data"]["stock_chart"]["dates"], ["2025-01-01", "2025-01-02"])
            self.assertEqual(data["data"]["stock_chart"]["prices"], [100, 101])

    @patch("app.routes.entities.get_stock_history")
    def test_get_entity_stock_chart_custom_period(self, mock_get_stock_history):
        """✅ Test /<uuid>/chart endpoint with custom period"""
        mock_get_stock_history.return_value = {
            "dates": ["2025-01-01", "2025-01-02"],
            "prices": [200, 210],
            "performance": 5.0,
        }

        with test_db() as client:
            entity = self._create_sample_entities()
            response = client.get(f"/api/entities/{entity.id}/chart?period=6M")
            
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["period"], "6M")
            self.assertEqual(data["data"]["stock_chart"]["prices"], [200, 210])

    def test_get_entity_stock_chart_entity_not_found(self):
        """✅ Test /<uuid>/chart with non-existent entity"""
        with test_db() as client:
            response = client.get(f"/api/entities/{uuid.uuid4()}/chart")
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertEqual(data["message"], "Entity not found")

    # Test cases for GET /api/ticker=^IRX/chart

    @patch("app.routes.entities.get_stock_history")
    def test_get_irx_chart_default_period(self, mock_get_stock_history):
        """✅ Test /ticker=^IRX/chart with default period"""
        mock_get_stock_history.return_value = {
            "dates": ["2025-01-01", "2025-01-02"],
            "prices": [4.5, 4.6],
            "performance": 0.02,
        }

        with test_db() as client:
            response = client.get("/api/entities/ticker=^IRX/chart")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["ticker"], "^IRX")
            self.assertEqual(data["data"]["name"], "13 Week Treasury Bill")
            self.assertEqual(data["data"]["period"], "1Y")
            self.assertEqual(data["data"]["stock_chart"]["prices"], [4.5, 4.6])

    @patch("app.routes.entities.get_stock_history")
    def test_get_irx_chart_custom_period(self, mock_get_stock_history):
        """✅ Test /ticker=^IRX/chart with a custom period"""
        mock_get_stock_history.return_value = {
            "dates": ["2025-06-01", "2025-06-02"],
            "prices": [4.7, 4.8],
            "performance": 0.03,
        }

        with test_db() as client:
            response = client.get("/api/entities/ticker=^IRX/chart?period=6M")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["period"], "6M")
            self.assertEqual(data["data"]["stock_chart"]["prices"], [4.7, 4.8])

    # Test cases for GET /api/entities/<ticker>/fundamental
    @patch("app.routes.entities.get_stock_fundamentals")
    def test_get_entity_fundamental_success(self, mock_get_fundamentals):
        """✅ Test /<ticker>/fundamental returns mocked fundamentals"""
        mock_get_fundamentals.return_value = {
            "P/E": "15.2",
            "EPS (ttm)": "2.34",
            "Market Cap": "10B"
        }

        with test_db() as client:
            response = client.get("/api/entities/ALPHA/fundamental")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            self.assertEqual(data["data"]["ticker"], "ALPHA")
            self.assertEqual(data["data"]["fundamentals"]["P/E"], "15.2")
            self.assertEqual(data["data"]["fundamentals"]["EPS (ttm)"], "2.34")
            self.assertEqual(data["data"]["fundamentals"]["Market Cap"], "10B")

    @patch("app.routes.entities.get_stock_fundamentals")
    def test_get_entity_fundamental_empty(self, mock_get_fundamentals):
        """✅ Test /<ticker>/fundamental when fundamentals is empty"""
        mock_get_fundamentals.return_value = {}

        with test_db() as client:
            response = client.get("/api/entities/BETA/fundamental")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            self.assertEqual(data["data"]["ticker"], "BETA")
            self.assertEqual(data["data"]["fundamentals"], {})

    # Test cases for GET /api/entities/<ticker>/price
    @patch("app.routes.entities.get_stock_price")
    def test_get_stock_price_success(self, mock_get_price):
        """✅ Test /ticker/<ticker>/price returns mocked stock price"""
        mock_get_price.return_value = 123.45

        with test_db() as client:
            response = client.get("/api/entities/ticker/ALPHA/price")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            self.assertEqual(data["data"]["ticker"], "ALPHA")
            self.assertEqual(data["data"]["price"], 123.45)
            self.assertEqual(data["message"], "Stock price fetched successfully")

    @patch("app.routes.entities.get_stock_price")
    def test_get_stock_price_failure(self, mock_get_price):
        """✅ Test /ticker/<ticker>/price handles exceptions gracefully"""
        mock_get_price.side_effect = Exception("API error")

        with test_db() as client:
            response = client.get("/api/entities/ticker/ALPHA/price")
            self.assertEqual(response.status_code, 500)

            data = response.get_json()
            self.assertIsNone(data["data"])
            self.assertIn("Error fetching stock price", data["message"])