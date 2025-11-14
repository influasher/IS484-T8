import unittest
from app.models import News, LabelingQueue, QueueStatus
from app import db
from tests.test_routes.setup_mock_db import test_db
from jobs.backfill_features import backfill_features
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
import numpy as np

class BackfillFeaturesTestCase(unittest.TestCase):
    """Integration + Unit tests for backfill_features()"""
    def _seed_db(self):

        news_id = uuid.uuid4()

        # Seed News item
        news = News(
            id=news_id,
            title="Market surges as inflation cools",
            summary="The market reacts positively to cooling inflation data.",
            content="Stocks rose across the board as inflation figures came in lower than expected.",
            finbert_score=60.0,
            second_model_score=55.0,
            published_date=datetime.utcnow(),
            url="https://example.com/market-surges",
        )
        db.session.add(news)

        # Queue item with missing features (should be updated)
        q1 = LabelingQueue(
            news_id=news_id,
            text="The market reacts positively to cooling inflation data.",
            finbert_score=0.6,
            llm_score=0.55,
            model_type="user_feedback",
            disagreement_score=0.1,
            uncertainty_score=0.2,
            sampling_reason="test",
            priority=1,
            status=QueueStatus.COMPLETED,
            features_json=None,
            feature_names_json=None,
        )
        db.session.add(q1)

        # Queue item that already has features (should be skipped)
        q2 = LabelingQueue(
            news_id=news_id,
            text="Already has features",
            finbert_score=0.2,
            llm_score=0.3,
            model_type="user_feedback",
            disagreement_score=0.1,
            uncertainty_score=0.2,
            sampling_reason="test",
            priority=2,
            status=QueueStatus.COMPLETED,
            features_json=[0.1, 0.2, 0.3],
            feature_names_json=["f1", "f2", "f3"],
        )
        db.session.add(q2)

        db.session.commit()

    # def test_backfill_features_updates_missing_items(self):
    #     """Should populate features_json for missing items"""
    #     with test_db() as client:
    #         with client.application.app_context():  # 👈 ensure same app/db context
    #             self._seed_db()

    #             q_missing = [item for item in LabelingQueue.query.all() if not item.features_json][0]
    #             test_app = client.application  # the same Flask app used by test_db

    #             # Mock the feature builder
    #             mock_builder = MagicMock()
    #             mock_builder.build_single_sample_features.return_value = (
    #                 np.array([0.1, 0.2, 0.3]),  # shape (1,3), has .tolist()
    #                 ["f1", "f2", "f3"]            # feature names
    #             )

    #             with patch("jobs.backfill_features.Flask", return_value=test_app), \
    #                 patch("jobs.backfill_features.db.init_app", return_value=None), \
    #                 patch("jobs.backfill_features.SentimentFeatureBuilder", return_value=mock_builder), \
    #                 patch("jobs.backfill_features.db.session", db.session), \
    #                 patch("jobs.backfill_features.db", db):
    #                 backfill_features()

    #             # Refresh from DB

    #             all_items = LabelingQueue.query.all()
    #             for item in all_items:
    #                 print(">>>", item.id, item.features_json)

    #             updated_item = LabelingQueue.query.get(q_missing.id)
    #             print(updated_item.features_json, updated_item.feature_names_json, updated_item.id)
    #             self.assertIsNotNone(updated_item.features_json)
    #             self.assertIsInstance(updated_item.features_json, list)
    #             self.assertGreater(len(updated_item.features_json), 0)
    #             self.assertIsNotNone(updated_item.feature_names_json)
    #             self.assertGreater(len(updated_item.feature_names_json), 0)

    def test_backfill_skips_existing_features(self):
        """Should not overwrite existing feature entries"""
        with test_db() as client:
            with client.application.app_context():
                self._seed_db()
                q_existing = LabelingQueue.query.filter(LabelingQueue.features_json.isnot(None)).first()
                original_features = q_existing.features_json

                test_app = client.application  # the same Flask app used by test_db

                with patch("jobs.backfill_features.Flask", return_value=test_app), \
                    patch("jobs.backfill_features.db.init_app", return_value=None):
                    backfill_features()

                updated = LabelingQueue.query.get(q_existing.id)
                self.assertEqual(updated.features_json, original_features)


if __name__ == "__main__":
    unittest.main()
