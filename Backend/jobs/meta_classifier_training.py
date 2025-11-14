"""
Meta-Classifier Retraining Job

Trains a meta-classifier to optimally combine FinBERT and LLM predictions
based on human-labeled data from the active learning queue.

This job should run periodically (e.g., weekly) when enough new labels are available.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask

# Import config directly to avoid triggering app/__init__.py at module level
from app.config import config
from app.models import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MetaClassifierTrainer:
    """
    Train meta-classifier for sentiment ensemble
    """
    
    def __init__(self, app: Flask, archive_after_training: bool = True):
        self.app = app
        self.model = None
        self.model_type = "RandomForest"
        self.archive_after_training = archive_after_training
        
    def load_training_data(self) -> pd.DataFrame:
        """
        Load labeled data from database with automatic sanitization:
        - drops list/dict features
        - coerces values to float where possible
        """
        with self.app.app_context():
            from app.models.active_learning import LabelingQueue, AggregatedLabel, QueueStatus
            
            logger.info("Loading training data from database...")

            query = db.session.query(
                LabelingQueue.id,
                LabelingQueue.finbert_score,
                LabelingQueue.llm_score,
                LabelingQueue.model_type,
                LabelingQueue.disagreement_score,
                LabelingQueue.uncertainty_score,
                LabelingQueue.features_json,
                LabelingQueue.feature_names_json,
                AggregatedLabel.final_label,
                AggregatedLabel.vote_count,
                AggregatedLabel.agreement_rate
            ).join(
                AggregatedLabel,
                LabelingQueue.id == AggregatedLabel.queue_item_id
            ).filter(
                LabelingQueue.status == QueueStatus.COMPLETED
            ).all()
            
            if not query:
                logger.warning("No training data available")
                return pd.DataFrame()

            data = []
            for row in query:
                features_json = row.features_json or []
                feature_names = row.feature_names_json or []

                clean_features = {}

                # Clean each feature
                for name, value in zip(feature_names, features_json):

                    # Drop list or dict features (e.g., embeddings)
                    if isinstance(value, (list, dict)):
                        continue

                    # Coerce booleans → int
                    if isinstance(value, bool):
                        clean_features[name] = int(value)
                        continue

                    # Coerce None → 0
                    if value is None:
                        clean_features[name] = 0
                        continue

                    # Try converting strings to float
                    try:
                        clean_features[name] = float(value)
                    except Exception:
                        # If value cannot be converted, drop it
                        continue

                # Add core engineered features
                clean_features['finbert_score'] = row.finbert_score
                clean_features['llm_score'] = row.llm_score
                clean_features['disagreement_score'] = row.disagreement_score
                clean_features['uncertainty_score'] = row.uncertainty_score
                clean_features['vote_count'] = row.vote_count
                clean_features['agreement_rate'] = row.agreement_rate

                # Add label
                label_map = {'bullish': 1, 'neutral': 0, 'bearish': -1}
                clean_features['human_label'] = label_map.get(row.final_label.value, 0)

                data.append(clean_features)

            df = pd.DataFrame(data)
            logger.info(f"Loaded {len(df)} training samples")
            logger.info(f"Label distribution:\n{df['human_label'].value_counts()}")

            return df
    
    def prepare_features(self, df: pd.DataFrame):
        """
        Prepare feature matrix and labels with CONSISTENT ORDERING
        """
        # Get all feature columns except label
        feature_cols = [col for col in df.columns if col != 'human_label']
        
        # CRITICAL: Sort alphabetically for consistency with prediction
        feature_cols = sorted(feature_cols)
        
        # Handle missing values
        df_clean = df[feature_cols].fillna(0)
        
        X = df_clean.values
        y = df['human_label'].values
        
        logger.info(f"Feature matrix shape: {X.shape}")
        logger.info(f"Feature order (first 10): {feature_cols[:10]}")
        logger.info(f"Total features: {len(feature_cols)}")
        
        return X, y, feature_cols
    
    def train_model(self, X, y):
        """
        Train meta-classifier

        X = Feature matrix (each row is a feature vector like above)
        y = Human labels (-1=bearish, 0=neutral, 1=bullish)

        Example data:
        Article 1: FinBERT says bullish (0.7), Gemini says neutral (0.1), is_financial_heavy=1
                    Human labeled: BULLISH (1)
                    → Model learns: "Trust FinBERT more on financial-heavy content"

        Article 2: FinBERT says bearish (-0.3), Gemini says bearish (-0.5), both_confident=1
                    Human labeled: BEARISH (-1)
                    → Model learns: "When both agree and are confident, trust the consensus"

        Article 3: FinBERT says bullish (0.4), Gemini says bearish (-0.4), score_difference=0.8
                    Human labeled: NEUTRAL (0)
                    → Model learns: "High disagreement often means neutral/uncertain"

        Train Random Forest classifier
        self.model = RandomForestClassifier(n_estimators=100, max_depth=10)
        self.model.fit(X, y)

        Model now "knows" patterns like:
        - "is_financial_heavy=1 + finbert_confident=1 → weight FinBERT more"
        - "score_difference > 0.6 → likely neutral"
        - "both_confident=1 + classifications_agree=1 → trust consensus"
        """
        logger.info(f"Training {self.model_type} meta-classifier...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Initialize model
        if self.model_type == "RandomForest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'  # Handle imbalanced data
            )
        elif self.model_type == "GradientBoosting":
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        else:  # LogisticRegression
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'
            )
        
        # Train
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Test Accuracy: {accuracy:.4f}")
        logger.info(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")
        logger.info(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='accuracy')
        logger.info(f"Cross-validation scores: {cv_scores}")
        logger.info(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        return {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
    
    def archive_training_data(self, df: pd.DataFrame, model_version: str):
        """
        Archive training data to CSV for record-keeping
        """
        try:
            # Create archives directory
            archives_dir = os.path.join(os.path.dirname(__file__), '..', 'archives', 'training_data')
            os.makedirs(archives_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = os.path.join(archives_dir, f'training_data_{model_version}_{timestamp}.csv')
            
            # Save full training data
            df.to_csv(archive_path, index=False)
            
            logger.info(f"Training data archived to: {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"Failed to archive training data: {e}")
            return None

    def save_model(self, feature_names, metrics, training_df: pd.DataFrame = None):
        """
        Save trained model and metadata
        """
        with self.app.app_context():
            # Import ModelRun INSIDE app context
            from app.models.active_learning import ModelRun
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create models directory
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'meta_classifier')
            os.makedirs(models_dir, exist_ok=True)
            
            # Save model file
            model_path = os.path.join(models_dir, f'meta_classifier_{timestamp}.joblib')
            model_version = f"{self.model_type}_{timestamp}"
            
            joblib.dump({
                'model': self.model,
                'feature_names': feature_names,
                'model_type': self.model_type,
                'trained_at': datetime.now().isoformat(),
                'metrics': metrics,
                'training_samples': len(training_df) if training_df is not None else 0
            }, model_path)
            
            logger.info(f"Model saved to: {model_path}")
            
            # Archive training data
            archive_path = None
            if self.archive_after_training and training_df is not None:
                archive_path = self.archive_training_data(training_df, model_version)
            
            # Record training run in database
            model_run = ModelRun(
                model_version=model_version,
                artifact_path=model_path,
                training_samples=len(training_df) if training_df is not None else 0,
                performance_metrics=metrics,
                is_active=True
            )
            
            # Deactivate previous models
            ModelRun.query.update({'is_active': False})
            
            db.session.add(model_run)
            db.session.commit()
            
            logger.info(f"Model run recorded in database (ID: {model_run.id})")
            
            return model_path, archive_path
    
    def run(self):
        """
        Execute full training pipeline
        """
        logger.info("=" * 80)
        logger.info("Starting Meta-Classifier Training Job")
        logger.info("=" * 80)
        
        try:
            # Load data
            df = self.load_training_data()
            
            if df.empty:
                logger.warning("No training data available. Exiting.")
                return
            
            # Check minimum samples
            if len(df) < 20:
                logger.warning(f"Insufficient training data ({len(df)} samples). Need at least 20.")
                return
            
            # Prepare features
            X, y, feature_names = self.prepare_features(df)
            
            # Train model
            metrics = self.train_model(X, y)
            
            # Save model (pass df for archiving)
            model_path, archive_path = self.save_model(feature_names, metrics, df)
            
            logger.info("=" * 80)
            logger.info("Meta-Classifier Training Completed Successfully")
            logger.info(f"Model saved to: {model_path}")
            if archive_path:
                logger.info(f"Training data archived to: {archive_path}")
            logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}", exc_info=True)
            raise


def create_app():
    """Create Flask app for job context - same pattern as other jobs"""
    app = Flask(__name__)
    
    # Load configuration - import directly to avoid triggering app/__init__.py
    env = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    # Initialize only database
    db.init_app(app)
    
    return app


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train meta-classifier')
    parser.add_argument('--no-archive', action='store_true', 
                       help='Skip archiving training data')
    
    args = parser.parse_args()
    
    app = create_app()
    trainer = MetaClassifierTrainer(app, archive_after_training=not args.no_archive)
    trainer.run()


if __name__ == '__main__':
    main()

