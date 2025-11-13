import unittest
import json
from app.routes.active_learning import to_uuid_safe
from tests.test_routes.setup_mock_db import test_db
from flask_jwt_extended import create_access_token
from app.models import *
from app import db
import datetime
import uuid
import io
from unittest.mock import patch, MagicMock

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

        user = User(
            id=uuid.uuid4(),  
            username="testuser2",
            email="test2@example.com",
            first_name="Test",
            last_name="User2",
            role="CLIENT"
        )
        db.session.add(user)
        db.session.commit()

        # now you can safely add votes
        vote1 = UserVote(queue_item_id=item1.id, news_id = item1.news_id, user_id=test_user.id, vote=SentimentVote.BULLISH)
        vote2 = UserVote(queue_item_id=item2.id, news_id = item2.news_id, user_id=test_user.id, vote=SentimentVote.BEARISH)
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

        stats = UserStats(
            user_id=test_user.id,
            total_votes=10,
            gold_standard_correct=8,
            gold_standard_total=10,
            reliability_score=0.8
        )
        db.session.add(stats)
        db.session.commit()

        # JWT for RM
        self.user_token = create_access_token(identity=str(test_user.id))
        self.user_token2 = create_access_token(identity=str(user.id))
        self.item_id = item1.id
        self.user_id = test_user.id
        self.user_id2 = user.id

        self.news_id = item1.news_id

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

    def test_to_uuid_safe_none(self):
        self.assertIsNone(to_uuid_safe(None))

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

    def test_get_user_stats_existing(self):
        """Test /user/<id>/stats returns correct stats for a user."""
        with test_db() as client:
            self._seed_labeling_queue()

            res = client.get(f"/api/labeling/user/{self.user_id}/stats", headers={"Authorization": f"Bearer {self.user_token}"})
            data = res.get_json()["data"]

            self.assertEqual(res.status_code, 200)
            self.assertEqual(data["total_votes"], 10)
            self.assertEqual(data["gold_standard_correct"], 8)
            self.assertEqual(data["reliability_score"], 0.8)

    def test_get_user_stats_default(self):
        # User without stats
        with test_db() as client:
            self._seed_labeling_queue()
            res = client.get(f"/api/labeling/user/{self.user_id2}/stats", headers={"Authorization": f"Bearer {self.user_token2}"})
            data = res.get_json()["data"]

            self.assertEqual(res.status_code, 200)
            self.assertEqual(data["total_votes"], 0)
            self.assertEqual(data["reliability_score"], 1.0)

    def test_get_all_user_statistics(self):
        with test_db() as client:
            self._seed_labeling_queue()
            # Add multiple users and stats
            stats1 = UserStats(
                user_id=self.user_id2,
                total_votes=5,
                gold_standard_correct=4,
                gold_standard_total=5,
                reliability_score=0.8
            )
            db.session.add(stats1)
            db.session.commit()

            res = client.get("/api/labeling/users/statistics", headers={"Authorization": f"Bearer {self.user_token}"})
            data = res.get_json()["data"]

            self.assertEqual(res.status_code, 200)
            self.assertTrue(len(data) >= 1)
            user_data = next(u for u in data if u["user_id"] == str(self.user_id2))
            self.assertEqual(user_data["total_votes"], 5)
            self.assertEqual(user_data["gold_standard_correct"], 4)
            self.assertEqual(user_data["agreement_with_majority"], 0.85)  # placeholder

    def test_enqueue_batch_items(self):
        """Test adding multiple items to the queue."""
        with test_db() as client:
            batch_payload = {"items": [
                {
                    "news_id": "123",
                    "text": "Test text",
                    "finbert_score": 0.5,
                    "llm_score": 0.7,
                    "model_type": "gemini",
                    "disagreement_score": 0.3,
                    "uncertainty_score": 0.4,
                    "sampling_reason": "test",
                    "priority": 5
                },
                {
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
            ]}
            response = client.post("/api/labeling/enqueue/batch", data=json.dumps(batch_payload), content_type="application/json")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(len(response.get_json()["data"]), 2)

    ##### /vote ######
    def test_vote_and_finalize_queue_item(self):
        """Test voting and finalization of a queue item."""
        with test_db() as client:
            self._seed_labeling_queue()
            
            payload = {"queue_item_id": self.item_id, "vote": "bullish"}
            response = client.post("/api/labeling/vote", json=payload, headers={"Authorization": f"Bearer {self.user_token2}"})

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json()["data"]["vote"], "bullish")

            finalize_response = client.post(f"/api/labeling/finalize/{self.item_id}")
            self.assertEqual(finalize_response.status_code, 200)
            self.assertEqual(finalize_response.get_json()["data"]["final_label"], "bullish")

    def test_user_has_voted(self):
        """Test submitting a vote on a queued item"""
        with test_db() as client:
            self._seed_labeling_queue()
            payload = {"queue_item_id": self.item_id, "vote": "bullish"}
            response = client.post("/api/labeling/vote", json=payload, headers={"Authorization": f"Bearer {self.user_token}"})
            data = response.get_json()
            self.assertEqual(response.status_code, 400)
            self.assertEqual(data["message"], "User has already voted on this item")
            self.assertIsNone(data["data"])

    def test_vote_invalid_value(self):
        """Vote with invalid value should return 400"""
        with test_db() as client:
            self._seed_labeling_queue()
            payload = {"queue_item_id": self.item_id, "vote": "invalid_vote"}
            headers = {"Authorization": f"Bearer {self.user_token}"}
            response = client.post("/api/labeling/vote", json=payload, headers=headers)
            self.assertEqual(response.status_code, 400)

    def test_finalize_insufficient_votes(self):
        """Finalize item fails when votes < MIN_VOTES_FOR_FINALIZATION"""
        with test_db() as client:
            item3 = LabelingQueue(
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
            db.session.add(item3)
            db.session.commit()

            finalize_response = client.post(f"/api/labeling/finalize/{item3.id}")
            data = finalize_response.get_json()

            self.assertEqual(finalize_response.status_code, 400)
            self.assertEqual(data["message"], "Cannot finalize item - insufficient votes or already finalized")
            self.assertIsNone(data["data"])

    def test_reset_votes_endpoint(self):
        """Test resetting all user votes."""
        with test_db() as client:
            self._seed_labeling_queue()
            payload = {"confirm": True}
            response = client.post("/api/labeling/reset-votes", json=payload, headers={"Authorization": f"Bearer {self.user_token}"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(UserVote.query.count(), 0)

    def test_clear_pending_queue(self):
        """Test clearing all pending items."""
        with test_db() as client:
            self._seed_labeling_queue()
            payload = {"confirm": True}
            response = client.post("/api/labeling/clear-queue", json=payload, headers={"Authorization": f"Bearer {self.user_token}"})
            self.assertEqual(response.status_code, 200)
            remaining = LabelingQueue.query.filter_by(status=QueueStatus.PENDING).count()
            self.assertEqual(remaining, 0)


    def test_no_votes_returns_empty_list(self):
        with test_db() as client:
            news_id = "news-123"
            res = client.get(f"/api/labeling/votes/news/{news_id}")
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertEqual(data["data"], [])

    def test_votes_found_by_news_id(self):
        with test_db() as client:
            self._seed_labeling_queue()
            res = client.get(f"/api/labeling/votes/news/{self.news_id}")
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(data["data"]), 1)
            self.assertEqual(data["data"][0]["vote"], "bullish")
            self.assertEqual(data["data"][0]["user_id"], str(self.user_id))

    def test_votes_found_via_queue_item(self):
        with test_db() as client:
            self._seed_labeling_queue()
            news_id = "news-101"
            queue_item = LabelingQueue(
                news_id=news_id,
                text="Sample article",
                finbert_score=0.5,
                llm_score=0.7,
                model_type="gemini",
                disagreement_score=0.2,
                uncertainty_score=0.3,
                sampling_reason="test",
                priority=1,
                status="COMPLETED",
                created_at=datetime.datetime.utcnow()
            )
            db.session.add(queue_item)
            db.session.commit()

            vote = UserVote(
                user_id=self.user_id,
                queue_item_id=queue_item.id,
                vote=SentimentVote.NEUTRAL,
                vote_time=datetime.datetime.utcnow()
            )
            db.session.add(vote)
            db.session.commit()

            res = client.get(f"/api/labeling/votes/news/{news_id}")
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(data["data"]), 1)
            self.assertEqual(data["data"][0]["vote"], "neutral")


    def test_export_labeled_data_success(self):
        with test_db() as client:
            self._seed_labeling_queue()
            
            response = client.get("/api/labeling/export")
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/csv", response.content_type)

            csv_content = io.StringIO(response.data.decode('utf-8'))
            lines = csv_content.readlines()
            self.assertGreaterEqual(len(lines), 2)  # header + at least one data row
            self.assertIn("bearish", lines[1].lower())
 
    def test_get_export_stats_success(self):
        with test_db() as client:
            self._seed_labeling_queue()
            
            # Add a last model run
            last_run = ModelRun(
                model_version="v1.0",       # cannot be None
                artifact_path="/path/to/artifact",
                training_samples=100,
                created_at=datetime.datetime.utcnow(),
                is_active=False
            )            
            db.session.add(last_run)
            db.session.commit()

            response = client.get("/api/labeling/export/stats")
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("total_completed", data["data"])
            self.assertIn("label_distribution", data["data"])
            self.assertIn("ready_for_retraining", data["data"])

    def test_training_history_with_runs(self):
        """Returns model runs in descending order of creation"""
        with test_db() as client:
            self._seed_labeling_queue()
            # Insert sample runs
            run1 = ModelRun(
                model_version="v1.0",
                artifact_path="/path/to/artifact1",
                training_samples=100,
                performance_metrics={"accuracy": 0.9},
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1),
                is_active=False
            )
            run2 = ModelRun(
                model_version="v1.1",
                artifact_path="/path/to/artifact2",
                training_samples=150,
                performance_metrics={"accuracy": 0.92},
                created_at=datetime.datetime.utcnow(),
                is_active=True
            )
            db.session.add_all([run1, run2])
            db.session.commit()

            response = client.get("/api/labeling/training-history")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            results = data["data"]

            # Check ordering (most recent first)
            self.assertEqual(results[0]["model_version"], "v1.1")
            self.assertEqual(results[1]["model_version"], "v1.0")

            # Check keys
            expected_keys = [
                "id", "model_version", "created_at",
                "training_samples", "performance_metrics",
                "is_active", "artifact_path"
            ]
            for run_data in results:
                self.assertTrue(all(key in run_data for key in expected_keys))
    
    def test_delete_nonexistent_model(self):
        """Deleting a model that doesn't exist returns 404"""
        with test_db() as client:
            self._seed_labeling_queue()
            response = client.post("/api/labeling/delete-model/999")
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertEqual(data["message"], "Model not found")

    def test_delete_active_model(self):
        """Cannot delete a model that is active"""
        with test_db() as client:
            self._seed_labeling_queue()
            model = ModelRun(
                model_version="v1.0",
                artifact_path=None,
                training_samples=100,
                is_active=True
            )
            db.session.add(model)
            db.session.commit()

            response = client.post(f"/api/labeling/delete-model/{model.id}")
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertEqual(data["message"], "Cannot delete the active model")

    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_delete_model_file_and_record(self, mock_remove, mock_exists):
        """Deletes model file and DB record for an inactive model"""
        with test_db() as client:
            self._seed_labeling_queue()
            model = ModelRun(
                model_version="v0.9",
                artifact_path="/fake/path/model.pkl",
                training_samples=50,
                is_active=False
            )
            db.session.add(model)
            db.session.commit()

            response = client.post(f"/api/labeling/delete-model/{model.id}")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["deleted_model_id"], model.id)

            # Ensure file deletion was attempted
            mock_exists.assert_called_once_with("/fake/path/model.pkl")
            mock_remove.assert_called_once_with("/fake/path/model.pkl")

            # Ensure DB record is deleted
            deleted_model = ModelRun.query.filter_by(id=model.id).first()
            self.assertIsNone(deleted_model)

    def test_delete_model_without_file(self):
        """Deletes model record if artifact_path does not exist"""
        with test_db() as client:
            self._seed_labeling_queue()
            model = ModelRun(
                model_version="v0.8",
                artifact_path=None,
                training_samples=30,
                is_active=False
            )
            db.session.add(model)
            db.session.commit()

            response = client.post(f"/api/labeling/delete-model/{model.id}")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["deleted_model_id"], model.id)

            # Ensure DB record is deleted
            deleted_model = ModelRun.query.filter_by(id=model.id).first()
            self.assertIsNone(deleted_model)

    # --- 1️⃣ Case: Not enough data for retraining ---
    def test_trigger_retrain_not_enough_data(self):
        with test_db() as client:
            for i in range(5):
                db.session.add(LabelingQueue(
                    news_id=f"n{i}",
                    text=f"text {i}",
                    finbert_score=0.5,
                    llm_score=0.6,
                    model_type="openai",
                    disagreement_score=0.1,
                    uncertainty_score=0.2,
                    sampling_reason="test",
                    priority=3,
                    status=QueueStatus.COMPLETED
                ))
            db.session.commit()

            response = client.post("/api/labeling/trigger-retrain")
            data = response.get_json()

            self.assertEqual(response.status_code, 400)
            self.assertIn("Not enough labeled data", data["message"])


    # --- 2️⃣ Missing training script ---
    @patch("os.path.exists", return_value=False)
    def test_trigger_retrain_missing_script(self, mock_exists):
        with test_db() as client:
            for i in range(25):
                db.session.add(LabelingQueue(
                news_id=f"n{i}",
                text=f"text {i}",
                finbert_score=0.5,
                llm_score=0.6,
                model_type="openai",
                disagreement_score=0.1,
                uncertainty_score=0.2,
                sampling_reason="test",
                priority=3,
                status=QueueStatus.COMPLETED
            ))
            db.session.commit()

            response = client.post("/api/labeling/trigger-retrain")
            data = response.get_json()

            self.assertEqual(response.status_code, 500)
            self.assertIn("Training script not found", data["message"])

    # --- 3️⃣ Case: Training starts successfully ---
    @patch("os.path.exists", return_value=True)
    @patch("threading.Thread")
    def test_trigger_retrain_success(self, mock_thread, client):
        """Ensure training thread starts when conditions are met"""
        with test_db() as client:
            for i in range(30):
                db.session.add(LabelingQueue(
                    news_id=f"n{i}",
                    text=f"text {i}",
                    finbert_score=0.5,
                    llm_score=0.6,
                    model_type="openai",
                    disagreement_score=0.1,
                    uncertainty_score=0.2,
                    sampling_reason="test",
                    priority=3,
                    status=QueueStatus.COMPLETED
                ))
            db.session.commit()

            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            response = client.post("/api/labeling/trigger-retrain")
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["data"]["status"], "training_started")
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()


    # --- 4️⃣ Internal error during execution ---
    @patch("os.path.exists", side_effect=Exception("Filesystem error"))
    def test_trigger_retrain_internal_error(self, mock_exists):
        with test_db() as client:
            for i in range(30):
                db.session.add(LabelingQueue(
                    news_id=f"n{i}",
                    text=f"text {i}",
                    finbert_score=0.5,
                    llm_score=0.6,
                    model_type="openai",
                    disagreement_score=0.1,
                    uncertainty_score=0.2,
                    sampling_reason="test",
                    priority=3,
                    status=QueueStatus.COMPLETED
                ))
            db.session.commit()

            response = client.post("/api/labeling/trigger-retrain")
            data = response.get_json()

            print(response.data)

            self.assertEqual(response.status_code, 500)
            self.assertIn("Failed to trigger retraining", data["message"])

    # --- 5️⃣ Enough new samples since last training ---
    @patch("os.path.exists", return_value=True)
    @patch("threading.Thread")
    def test_trigger_retrain_new_samples_since_last_training(self, mock_thread, mock_exists):
        with test_db() as client:
            last_run = ModelRun(
                model_version="v1",
                artifact_path="/tmp/fake.pkl",
                training_samples=10,
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1),
                is_active=True
            )
            db.session.add(last_run)
            db.session.commit()

            # ✅ Create 25 completed LabelingQueue items
            for i in range(25):
                item = LabelingQueue(
                    news_id=f"n{i}",
                    text=f"text {i}",
                    finbert_score=0.5,
                    llm_score=0.6,
                    model_type="openai",
                    disagreement_score=0.1,
                    uncertainty_score=0.2,
                    sampling_reason="test",
                    priority=3,
                    status=QueueStatus.COMPLETED
                )
                db.session.add(item)
                db.session.flush()  # ensures item.id is available for AggregatedLabel

                # ✅ Now create AggregatedLabel with valid FK
                db.session.add(AggregatedLabel(
                    queue_item_id=item.id,
                    final_label="BULLISH",
                    vote_count=3,
                    agreement_rate=1.0,
                    finalized_at=datetime.datetime.utcnow()
                ))
            db.session.commit()

            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            response = client.post("/api/labeling/trigger-retrain")
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["data"]["status"], "training_started")
            mock_thread_instance.start.assert_called_once()



if __name__ == "__main__":
    unittest.main()
