import unittest
import json
from app.routes.active_learning import to_uuid_safe
from tests.test_routes.setup_mock_db import test_db
from app.models import *
from app import db
import datetime
import uuid

class ActiveLearningTestCase(unittest.TestCase):
    def _seed_labeling_queue(self):
        # Add LabelingQueue items
        item1 = LabelingQueue(
            news_id="n1",
            text="Text 1",
            finbert_score=0.5,
            llm_score=0.7,
            model_type="gemini",
            disagreement_score=0.2,
            uncertainty_score=0.3,
            sampling_reason="test",
            priority=1,
            status=QueueStatus.PENDING,
            created_at=datetime.datetime.utcnow()
        )

        item2 = LabelingQueue(
            news_id="n2",
            text="Text 2",
            finbert_score=0.6,
            llm_score=0.8,
            model_type="gemini",
            disagreement_score=0.1,
            uncertainty_score=0.2,
            sampling_reason="test",
            priority=2,
            status=QueueStatus.COMPLETED,
            created_at=datetime.datetime.utcnow()
        )

        db.session.add_all([item1, item2])
        db.session.commit()

        # create a test user
        test_user = User(
            id=uuid.UUID("d08fe8b1-4066-4915-bd26-3f58da593ae1"),  # same UUID used in votes
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="CLIENT"
        )
        db.session.add(test_user)
        db.session.commit()

        # now you can safely add votes
        vote1 = UserVote(queue_item_id=item1.id, user_id=test_user.id, vote=SentimentVote.BULLISH)
        vote2 = UserVote(queue_item_id=item2.id, user_id=test_user.id, vote=SentimentVote.BEARISH)
        db.session.add_all([vote1, vote2])
        db.session.commit()

        # Add AggregatedLabel
        agg1 = AggregatedLabel(
            queue_item_id=item2.id,
            final_label=FinalSentiment.BEARISH,
            vote_count=1,
            agreement_rate=1.0,
            aggregation_method="majority",
            finalized_at=datetime.datetime.utcnow()
        )
        db.session.add(agg1)
        db.session.commit()


    # ---------- UNIT TESTS ----------

    def test_to_uuid_safe_valid(self):
        """Ensure to_uuid_safe converts valid UUID strings correctly."""
        import uuid
        valid_str = str(uuid.uuid4())
        result = to_uuid_safe(valid_str)
        self.assertIsInstance(result, uuid.UUID)

    def test_to_uuid_safe_invalid(self):
        """Ensure invalid UUID returns None instead of raising error."""
        result = to_uuid_safe("not-a-uuid")
        self.assertIsNone(result)

    # ---------- INTEGRATION TESTS (ROUTES) ----------

    def test_enqueue_item_success(self):
        """Test /enqueue successfully adds a queue item."""
        with test_db() as client:
            response = client.post(
                "/api/labeling/enqueue",
                json={
                    "news_id": "123",
                    "text": "Test text",
                    "finbert_score": 0.5,
                    "llm_score": 0.7,
                    "model_type": "gemini",
                    "disagreement_score": 0.3,
                    "uncertainty_score": 0.4,
                    "sampling_reason": "test",
                    "priority": 5
                }
            )

            print(">>>>", response.data)

            data = json.loads(response.data)
            self.assertEqual(response.status_code, 201)
            self.assertIn("Item enqueued successfully", data["message"])

    def test_enqueue_item_failure(self):
        """Test that /enqueue returns 500 and rolls back when DB commit fails."""
        with test_db() as client:
            # Intentionally insert an invalid record (missing non-nullable fields)
            bad_payload = {
                "text": None,  # violates NOT NULL constraint
                "finbert_score": 0.5,
                "llm_score": 0.5,
                "model_type": "openai",
                "disagreement_score": 0.1,
                "uncertainty_score": 0.1,
                "sampling_reason": "test",
                "priority": 1
            }

            response = client.post(
                "/api/labeling/enqueue",
                data=json.dumps(bad_payload),
                content_type="application/json"
            )

            # Since the route catches DB errors, assert the response instead of using assertRaises
            self.assertEqual(response.status_code, 500)
            self.assertIn("Failed to enqueue item", response.get_json()["message"])

    
    def test_get_aggregated_result_success(self):
        """Test /aggregate/<id> returns actual aggregated result from test DB."""
        with test_db() as client:
            # 1️⃣ Create a fake queue item
            queue_item = LabelingQueue(
                news_id="abc123",
                text="Stock prices rise amid optimism.",
                finbert_score=0.8,
                llm_score=0.7,
                model_type="openai",
                disagreement_score=0.1,
                uncertainty_score=0.1,
                sampling_reason="test",
                priority=1,
                status="COMPLETED"
            )
            db.session.add(queue_item)
            db.session.commit()

            # 2️⃣ Add an aggregated label tied to the queue item
            agg = AggregatedLabel(
                queue_item_id=queue_item.id,
                final_label=FinalSentiment.BULLISH,
                vote_count=3,
                agreement_rate=0.9,
                aggregation_method="majority"
            )
            db.session.add(agg)
            db.session.commit()

            # 3️⃣ Call the API
            response = client.get(f"/api/labeling/aggregate/{queue_item.id}")
            data = response.get_json()

            # 4️⃣ Verify
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["data"]["final_label"], "bullish")
            self.assertEqual(data["data"]["vote_count"], 3)
            self.assertEqual(data["data"]["agreement_rate"], 0.9)

    def test_get_system_stats(self):
        """Test /stats route aggregates counts."""
        with test_db() as client:
            self._seed_labeling_queue()
            
            # Call the stats endpoint
            response = client.get("/api/labeling/stats")
            data = json.loads(response.data)

            # --- Assertions ---
            self.assertEqual(response.status_code, 200)
            self.assertIn("pending_count", data["data"])
            self.assertIn("completed_count", data["data"])
            self.assertIn("high_priority_pending", data["data"])
            self.assertIn("total_votes", data["data"])
            self.assertIn("unique_users", data["data"])
            self.assertIn("avg_agreement_rate", data["data"])

            # Optional: check actual values
            self.assertEqual(data["data"]["pending_count"], 1)
            self.assertEqual(data["data"]["completed_count"], 1)
            self.assertEqual(data["data"]["total_votes"], 2)
            self.assertEqual(data["data"]["unique_users"], 1)
            self.assertAlmostEqual(data["data"]["avg_agreement_rate"], 1.0)

if __name__ == "__main__":
    unittest.main()
