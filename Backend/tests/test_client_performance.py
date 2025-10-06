import unittest
import sys
import os
from datetime import datetime, timezone, timedelta

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_dir)

from tests.test_config import BaseTestCase

try:
    # Try project-local imports similar to test_user_model.py
    from models.client_performance import ClientPerformance
    from models.user import User
    from extensions import db
    from sqlalchemy.exc import IntegrityError
except ImportError:
    # Fallback to app.* structure if available
    try:
        from app.models.client_performance import ClientPerformance  # type: ignore
        from app.models.user import User  # type: ignore
        from app import db  # type: ignore
        from sqlalchemy.exc import IntegrityError  # type: ignore
    except Exception:
        ClientPerformance = None
        User = None
        db = None
        IntegrityError = Exception


class ClientPerformanceModelTestCase(BaseTestCase):
    """Test cases for ClientPerformance model."""

    def setUp(self):
        super().setUp()
        if not (ClientPerformance and User and db):
            self.skipTest("ClientPerformance/User model or db not available")

    def _create_user(self, email='cp_test@example.com', username='cp_testuser'):
        user = User(email=email, username=username)
        if hasattr(user, 'set_password'):
            user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

    def test_create_client_performance(self):
        """Test creating a client performance record."""
        user = self._create_user()
        perf = ClientPerformance(
            client_uuid=user.id,
            daily_performance=1.25  # 1.25%
        )
        db.session.add(perf)
        db.session.commit()

        self.assertIsNotNone(perf.client_uuid)
        self.assertIsNotNone(perf.datetime)
        self.assertIsNotNone(perf.daily_performance)
        # Relationship
        self.assertIsNotNone(perf.client)
        self.assertEqual(str(perf.client.id), str(user.id))

    def test_to_dict(self):
        """Test serialization of client performance."""
        user = self._create_user()
        perf = ClientPerformance(
            client_uuid=user.id,
            daily_performance=-0.42
        )
        db.session.add(perf)
        db.session.commit()

        data = perf.to_dict()
        self.assertEqual(data.get('client_uuid'), str(user.id))
        self.assertIn('datetime', data)
        self.assertEqual(data.get('daily_performance'), -0.42)

    def test_repr(self):
        """Test string representation contains client and datetime."""
        user = self._create_user()
        perf = ClientPerformance(
            client_uuid=user.id,
            daily_performance=0.0
        )
        db.session.add(perf)
        db.session.commit()

        r = repr(perf)
        self.assertIn('ClientPerformance', r)
        self.assertIn(str(user.id), r)

    def test_composite_pk_uniqueness(self):
        """Test composite PK (client_uuid, datetime) enforces uniqueness."""
        user = self._create_user()
        fixed_dt = datetime.now(timezone.utc).replace(microsecond=0)

        perf1 = ClientPerformance(
            client_uuid=user.id,
            datetime=fixed_dt,
            daily_performance=0.1
        )
        db.session.add(perf1)
        db.session.commit()

        perf2 = ClientPerformance(
            client_uuid=user.id,
            datetime=fixed_dt,  # same composite key
            daily_performance=0.2
        )
        db.session.add(perf2)

        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_multiple_records_same_client_different_datetime(self):
        """Allow multiple records for same client at different datetimes."""
        user = self._create_user()
        base_dt = datetime.now(timezone.utc).replace(microsecond=0)

        perf1 = ClientPerformance(
            client_uuid=user.id,
            datetime=base_dt,
            daily_performance=0.1
        )
        perf2 = ClientPerformance(
            client_uuid=user.id,
            datetime=base_dt + timedelta(days=1),
            daily_performance=0.2
        )

        db.session.add(perf1)
        db.session.add(perf2)
        db.session.commit()

        # Query back and ensure both exist
        records = ClientPerformance.query.filter_by(client_uuid=user.id).all()
        self.assertEqual(len(records), 2)

if __name__ == '__main__':
    unittest.main()
