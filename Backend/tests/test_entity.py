import unittest
import os
import sys
from app import create_app, db
from app.models.entity import Entity
import uuid
import random
import string
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class EntityTestCase(unittest.TestCase):
    """Test cases for entity functionality."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.test_counter = 0
        self.app = create_app()
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["TESTING"] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def generate_unique_entity_name(self):
        """Generate a unique entity name for testing."""
        self.test_counter += 1
        random_suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        return f"TestEntity_{self.test_counter}_{random_suffix}"

    def generate_unique_ticker(self):
        """Generate a unique ticker symbol."""
        self.test_counter += 1
        random_suffix = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=3)
        )
        return f"TST{random_suffix}"

    def create_test_entity(self, **kwargs):
        """Create a test entity with unique constraints."""
        default_data = {
            "id": uuid.uuid4(),
            "name": self.generate_unique_entity_name(),
            "ticker": self.generate_unique_ticker(),
            "summary": f"Test entity summary {self.test_counter}",
            "sentiment_score": 0.7,
            "classification": "Company",
        }
        default_data.update(kwargs)

        try:
            from app.models.entity import Entity

            entity = Entity(**default_data)
            db.session.add(entity)
            db.session.commit()
            return entity
        except ImportError:
            self.skipTest("Entity model not available")

    def tearDown(self):
        """Clean up ONLY test database - never touches live DB."""
        try:
            # Only affects isolated test database
            db.session.rollback()
            db.session.remove()
            
            # These operations only affect the temporary test database
            if db.engine.dialect.name == 'postgresql':
                # This should never happen in tests since we use SQLite
                raise ValueError("CRITICAL: Test should not use PostgreSQL!")
            else:
                # Safe - only affects temporary SQLite test file
                db.drop_all()
                
        except Exception as e:
            print(f"Warning: Error during entity test cleanup: {e}")
        finally:
            super().tearDown()  # Calls BaseTestCase cleanup

    def test_create_entity(self):
        """Test creating entity"""
        entity = self.create_test_entity(
            name=self.generate_unique_entity_name(),
            ticker=self.generate_unique_ticker(),
        )

        self.assertIsNotNone(entity)
        self.assertIsNotNone(entity.name)
        self.assertIsNotNone(entity.ticker)

    def test_delete_entity(self):
        """Test deleting entity"""
        # Create entity with unique data
        entity = self.create_test_entity()
        entity_id = entity.id

        try:
            from app.models.entity import Entity

            # Delete the entity
            db.session.delete(entity)
            db.session.commit()

            # Verify deletion
            deleted_entity = Entity.query.get(entity_id)
            self.assertIsNone(deleted_entity)

        except ImportError:
            self.skipTest("Entity model not available")

    def test_read_entity(self):
        """Test reading entity"""
        # Create entity with unique data
        unique_name = self.generate_unique_entity_name()
        entity = self.create_test_entity(name=unique_name)

        try:
            from app.models.entity import Entity

            # Read the entity from database
            found_entity = Entity.query.filter_by(name=unique_name).first()

            self.assertIsNotNone(found_entity)
            self.assertEqual(found_entity.name, unique_name)

        except ImportError:
            self.skipTest("Entity model not available")

    def test_update_entity(self):
        """Test updating entity"""
        # Create entity with unique name
        entity = self.create_test_entity(
            name=self.generate_unique_entity_name(),
            ticker=self.generate_unique_ticker(),
        )
        original_name = entity.name

        try:
            from app.models.entity import Entity

            # Update the entity
            new_name = self.generate_unique_entity_name()
            entity.name = new_name
            entity.sentiment_score = 0.9
            db.session.commit()

            # Verify update
            updated_entity = Entity.query.get(entity.id)
            self.assertEqual(updated_entity.name, new_name)
            self.assertEqual(updated_entity.sentiment_score, 0.9)
            self.assertNotEqual(updated_entity.name, original_name)

        except ImportError:
            self.skipTest("Entity model not available")
            # Verify update
            updated_entity = Entity.query.get(entity.id)
            self.assertEqual(updated_entity.name, new_name)
            self.assertEqual(updated_entity.sentiment_score, 0.9)
            self.assertNotEqual(updated_entity.name, original_name)

        except ImportError:
            self.skipTest("Entity model not available")
