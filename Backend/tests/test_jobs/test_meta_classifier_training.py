import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd

from app import db
from tests.test_routes.setup_mock_db import test_db
from app.models.active_learning import LabelingQueue, AggregatedLabel, QueueStatus, ModelRun
from jobs.meta_classifier_training import MetaClassifierTrainer


class TestMetaClassifierTrainerUnit(unittest.TestCase):
    def test_prepare_features_orders_columns_and_fills_nan(self):
        with test_db() as client:
            df = pd.DataFrame({
                'f3': [1, 2],
                'f1': [np.nan, 4],
                'f2': [5, 6],
                'human_label': [1, -1]
            })

            trainer = MetaClassifierTrainer(client.application)
            X, y, feature_cols = trainer.prepare_features(df)

            # Columns should be sorted alphabetically
            self.assertEqual(feature_cols, ['f1', 'f2', 'f3'])
            # NaNs should be filled
            self.assertTrue(np.all(X[0] == np.array([0, 5, 1])))
            # Labels unchanged
            self.assertTrue(np.array_equal(y, [1, -1]))

    def test_train_model_returns_metrics(self):
        with test_db() as client:
            trainer = MetaClassifierTrainer(client.application)
            X = np.random.rand(30, 5)
            y = np.random.choice([-1, 0, 1], size=30)
            metrics = trainer.train_model(X, y)
            self.assertIn('accuracy', metrics)
            self.assertIn('cv_mean', metrics)
            self.assertIn('cv_std', metrics)

    def test_archive_training_data_creates_path(self):
         with test_db() as client:
            trainer = MetaClassifierTrainer(client.application)
            df = pd.DataFrame({'a': [1, 2]})
            path = trainer.archive_training_data(df, "v1")
            self.assertTrue(path.endswith(".csv"))

    @patch('joblib.dump')
    def test_save_model_records_model_run(self, mock_joblib):
         with test_db() as client:
            trainer = MetaClassifierTrainer(client.application)
            trainer.model = MagicMock()
            df = pd.DataFrame({'f1': [0.1], 'human_label': [1]})

            with client.application.app_context():
                path, archive_path = trainer.save_model(['f1'], {'accuracy': 1.0}, df)
                model_run = ModelRun.query.first()
                self.assertIsNotNone(model_run)
                self.assertTrue(model_run.is_active)
                self.assertEqual(model_run.training_samples, 1)



class TestMetaClassifierTrainerIntegration(unittest.TestCase):
    """Full pipeline test with in-memory SQLite database"""

    def _seed_data(self):
        # Seed DB with completed queue items and aggregated labels
        for i in range(25):
            item = LabelingQueue(
                text="Example news content",           # <-- required
                finbert_score=np.random.rand(),
                llm_score=np.random.rand(),
                model_type="gemini",                   # required
                disagreement_score=0.0,                # required
                uncertainty_score=0.0,                 # required
                sampling_reason="unit_test",           # required
                priority=1,                            # required
                status=QueueStatus.COMPLETED,
                features_json=[0.1, 0.2],
                feature_names_json=['f1', 'f2']
            )
            db.session.add(item)
            db.session.flush()  # get id
            label = AggregatedLabel(
                queue_item_id=item.id,
                final_label=np.random.choice(['BULLISH','NEUTRAL','BEARISH']),
                vote_count=3,
                agreement_rate=0.7
            )
            db.session.add(label)
        db.session.commit()


    @patch('joblib.dump')
    @patch.object(MetaClassifierTrainer, 'archive_training_data', return_value=None)
    def test_full_training_pipeline(self, mock_archive, mock_joblib):
        with test_db() as client:
            self._seed_data()
            trainer = MetaClassifierTrainer(client.application, archive_after_training=True)
            trainer.model_type = "RandomForest"

            # Run full pipeline
            trainer.run()

            # Check model was created
            self.assertIsNotNone(trainer.model)
            # Ensure joblib.dump was called
            self.assertTrue(mock_joblib.called)
        
            runs = ModelRun.query.all()
            self.assertGreaterEqual(len(runs), 1)
            self.assertTrue(runs[0].is_active)


if __name__ == '__main__':
    unittest.main()
