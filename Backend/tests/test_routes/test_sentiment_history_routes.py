import unittest
from datetime import date
from app import db
from tests.test_routes.setup_mock_db import test_db
from app.models.sentiment_history import SentimentHistory
from app.models.entity import Entity
import uuid


class SentimentHistoryIntegrationTest(unittest.TestCase):
    """Full integration tests for Sentiment History routes"""
    def _create_sample_entities(self):
        # Create sample entity
        entity = Entity(
            id=uuid.uuid4(),
            name="Alpha Corp",
            ticker="ALPHA"
        )
        db.session.add(entity)
        db.session.commit()
        self.entity = entity

    # -------------------------------------------------------------------------
    # GET /api/sentiment-history/
    # -------------------------------------------------------------------------
    def test_get_sentiment_history_success(self):
        """Should return sentiment history for a given entity_id"""
        with test_db() as client:
            self._create_sample_entities()
            record = SentimentHistory(
                entity_id=self.entity.id,
                date=date(2025, 10, 31),
                sentiment_score=0.85
            )
            db.session.add(record)
            db.session.commit()

            response = client.get(
                f"/api/sentiment_history/?entity_id={self.entity.id}"
            )
            data = response.get_json()
            print(data)

            self.assertEqual(response.status_code, 200)
            self.assertIn("fetched successfully", data["message"])
            self.assertEqual(len(data["data"]["sentiment_history"]), 1)
            self.assertEqual(data["data"]["sentiment_history"][0]["sentiment_score"], 0.85)

    # -------------------------------------------------------------------------
    # POST /api/sentiment-history/
    # -------------------------------------------------------------------------
    def test_create_sentiment_history_success(self):
        """Should create a sentiment history record"""
        with test_db() as client:
            self._create_sample_entities()
            payload = {
                "entity_id": str(self.entity.id),
                "sentiment_score": 0.92
            }

            response = client.post(
                "/api/sentiment_history/",
                json=payload
            )

            data = response.get_json()
            self.assertEqual(response.status_code, 201)
            self.assertIn("created successfully", data["message"])

            # Check DB
            record = SentimentHistory.query.filter_by(entity_id=self.entity.id).first()
            self.assertIsNotNone(record)
            self.assertAlmostEqual(record.sentiment_score, 0.92)

    def test_create_sentiment_history_missing_fields(self):
        """Should return 400 when required fields missing"""
        with test_db() as client:
            self._create_sample_entities()
            payload = {"entity_id": str(self.entity.id)}  # missing sentiment_score
            response = client.post("/api/sentiment_history/", json=payload)

            data = response.get_json()
            self.assertEqual(response.status_code, 400)
            self.assertEqual(data["message"], "Missing required fields")

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    def test_create_and_get_flow(self):
        """End-to-end: create → fetch same record"""
        with test_db() as client:
            self._create_sample_entities()
            payload = {
                "entity_id": str(self.entity.id),
                "sentiment_score": 0.7
            }
            post_resp = client.post("/api/sentiment_history/", json=payload)
            self.assertEqual(post_resp.status_code, 201)

            get_resp = client.get(f"/api/sentiment_history/?entity_id={self.entity.id}")
            data = get_resp.get_json()

            self.assertEqual(get_resp.status_code, 200)
            self.assertAlmostEqual(data["data"]["sentiment_history"][0]["sentiment_score"], 0.7)

