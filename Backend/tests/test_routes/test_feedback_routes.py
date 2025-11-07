import unittest
import uuid
from app.models import Feedback, User, News
from app import db
from tests.test_routes.setup_mock_db import test_db
from datetime import datetime
from sqlalchemy.exc import IntegrityError

class FeedbackIntegrationTest(unittest.TestCase):

    def _create_sample_data(self):
        """Seed test DB with a user, news, and feedback."""
        user = User(
            id=uuid.uuid4(),
            username="alice123",
            email="alice@example.com",
            first_name="Alice",
            last_name="Liddell",
            role="RELATIONSHIP_MANAGER",
        )
        news = News(
            id=uuid.uuid4(),
            publisher="TechDaily",
            title="Tesla launches new AI chip",
            description="Tesla has announced the release of a new AI chip for self-driving vehicles.",
            url="https://techdaily.com/news/tesla-ai-chip",
            published_date=datetime(2025, 1, 10, 10, 30)
        )

        db.session.add(user)
        db.session.add(news)
        db.session.commit()

        print(user, news, user.id, news.id)

        feedback = Feedback(
            id=uuid.uuid4(),
            userID=user.id,
            newsID=news.id,
            assessment="Bullish"
        )
        print(">>>", feedback)
        db.session.add(feedback)
        db.session.commit()

        return user, news, feedback

    # -------------------- GET Feedback by User --------------------
    def test_get_feedback_by_user_success(self):
        with test_db() as client:
            user, news, feedback = self._create_sample_data()
            response = client.get(f"/api/feedback/user/{user.id}")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            self.assertEqual(data["data"][0]["assessment"], "Bullish")
            self.assertEqual(data["message"], "Feedback fetched successfully")

    def test_get_feedback_by_user_not_found(self):
        with test_db() as client:
            fake_user_id = uuid.uuid4()
            response = client.get(f"/api/feedback/user/{fake_user_id}")
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertEqual(data["message"], "Feedback not found")
            self.assertIsNone(data["data"])

    # -------------------- GET Feedback by News --------------------
    def test_get_feedback_by_news_success(self):
        with test_db() as client:
            user, news, feedback = self._create_sample_data()
            response = client.get(f"/api/feedback/news/{news.id}")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"][0]["assessment"], "Bullish")

    def test_get_feedback_by_news_not_found(self):
        with test_db() as client:
            fake_news_id = uuid.uuid4()
            response = client.get(f"/api/feedback/news/{fake_news_id}")
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertIsNone(data["data"])
            self.assertEqual(data["message"], "Feedback not found")

    # -------------------- GET Feedback by User and News --------------------
    def test_get_feedback_by_user_and_news_success(self):
        with test_db() as client:
            user, news, feedback = self._create_sample_data()
            response = client.get(f"/api/feedback/user/{user.id}/news/{news.id}")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["assessment"], "Bullish")

    def test_get_feedback_by_user_and_news_not_found(self):
        with test_db() as client:
            fake_user_id = uuid.uuid4()
            fake_news_id = uuid.uuid4()
            response = client.get(f"/api/feedback/user/{fake_user_id}/news/{fake_news_id}")
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertIsNone(data["data"])

    # -------------------- POST Feedback --------------------
    def test_create_feedback_success(self):
        with test_db() as client:
            user, news, _ = self._create_sample_data()
            payload = {
                "userID": str(user.id),
                "newsID": str(news.id),
                "assessment": "Bearish"
            }
            response = client.post("/api/feedback/", json=payload)
            self.assertEqual(response.status_code, 201)
            data = response.get_json()
            self.assertEqual(data["data"]["assessment"], "Bearish")
            self.assertEqual(data["message"], "Feedback created successfully")

    def test_create_feedback_missing_fields(self):
        with test_db() as client:
            payload = {
                "userID": str(uuid.uuid4()),
                # Missing newsID and assessment
            }

            with self.assertRaises(IntegrityError):
                client.post(
                    "/api/feedback/",
                    json=payload,
                )
            

    