# import unittest
# import sys
# import os
# import uuid
# import random
# import string
# from datetime import datetime, timezone, timedelta

# # Add backend directory to Python path
# backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# sys.path.insert(0, backend_dir)

# from tests.test_config import BaseTestCase

# try:
#     from models.client_portfolio import ClientPortfolio
#     from models.user import User
#     from models.entity import Entity
#     from extensions import db
#     from sqlalchemy.exc import IntegrityError
# except ImportError:
#     ClientPortfolio = None
#     User = None
#     Entity = None
#     db = None
#     IntegrityError = Exception


# class ClientPortfolioModelTestCase(BaseTestCase):
#     """Test cases for ClientPortfolio model."""

#     def setUp(self):
#         super().setUp()
#         if not all([ClientPortfolio, User, Entity, db]):
#             self.skipTest("ClientPortfolio/User/Entity model or db not available")

#     def _rand(self, n=6):
#         return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

#     def _create_user(self, email=None, username=None):
#         email = email or f'cp_{self._rand()}@example.com'
#         username = username or f'cp_user_{self._rand()}'
#         user = User(email=email, username=username)
#         if hasattr(user, 'set_password'):
#             user.set_password('password123')
#         db.session.add(user)
#         db.session.commit()
#         return user

#     def _create_entity(self, name=None, ticker=None):
#         name = name or f'TestEntity_{self._rand()}'
#         ticker = ticker or f'T{self._rand(3)}'.upper()
#         entity = Entity(name=name, ticker=ticker)
#         db.session.add(entity)
#         db.session.commit()
#         return entity

#     def test_create_client_portfolio(self):
#         """Create a portfolio record and verify relationships."""
#         user = self._create_user()
#         entity = self._create_entity()

#         cp = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=10)
#         db.session.add(cp)
#         db.session.commit()

#         self.assertIsNotNone(cp.user_id)
#         self.assertIsNotNone(cp.entity_id)
#         self.assertEqual(cp.qty, 10)
#         self.assertIsNotNone(cp.user)
#         self.assertIsNotNone(cp.entity)
#         self.assertEqual(str(cp.user.id), str(user.id))
#         self.assertEqual(str(cp.entity.id), str(entity.id))

#     def test_to_dict(self):
#         """Verify to_dict serialization."""
#         user = self._create_user()
#         entity = self._create_entity()

#         cp = ClientPortfolio(
#             user_id=user.id,
#             entity_id=entity.id,
#             qty=5,
#             current_price=100.0,
#             total_invested=450.0,
#             first_purchase_date=datetime.now(timezone.utc) - timedelta(days=10),
#             last_transaction_date=datetime.now(timezone.utc),
#         )
#         cp.calculate_current_values()  # sets current_market_value and pnl
#         db.session.add(cp)
#         db.session.commit()

#         data = cp.to_dict()
#         self.assertEqual(data.get('user_id'), str(user.id))
#         self.assertEqual(data.get('entity_id'), str(entity.id))
#         self.assertEqual(data.get('qty'), 5)
#         self.assertIn('current_market_value', data)
#         self.assertIn('unrealized_pnl', data)
#         self.assertIn('first_purchase_date', data)
#         self.assertIn('last_transaction_date', data)

#     def test_repr(self):
#         """__repr__ contains user and entity IDs."""
#         user = self._create_user()
#         entity = self._create_entity()
#         cp = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=1)
#         db.session.add(cp)
#         db.session.commit()

#         r = repr(cp)
#         self.assertIn(str(user.id), r)
#         self.assertIn(str(entity.id), r)

#     def test_composite_pk_uniqueness(self):
#         """Composite PK (user_id, entity_id) must be unique."""
#         user = self._create_user()
#         entity = self._create_entity()

#         cp1 = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=10)
#         db.session.add(cp1)
#         db.session.commit()

#         cp2 = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=20)
#         db.session.add(cp2)

#         with self.assertRaises(IntegrityError):
#             db.session.commit()
#         db.session.rollback()

#     def test_calculate_current_values(self):
#         """current_market_value and PnL calculations."""
#         user = self._create_user()
#         entity = self._create_entity()
#         cp = ClientPortfolio(
#             user_id=user.id,
#             entity_id=entity.id,
#             qty=5,
#             current_price=100.0,
#             total_invested=400.0,
#         )
#         cp.calculate_current_values()
#         db.session.add(cp)
#         db.session.commit()

#         self.assertEqual(cp.current_market_value, 500.0)
#         self.assertEqual(cp.unrealized_pnl, 100.0)
#         self.assertAlmostEqual(cp.unrealized_pnl_percent, 25.0, places=4)

#     def test_holding_period_and_long_term(self):
#         """Holding period days and long-term flag."""
#         user = self._create_user()
#         entity = self._create_entity()
#         old_date = datetime.now(timezone.utc) - timedelta(days=400)

#         cp = ClientPortfolio(
#             user_id=user.id,
#             entity_id=entity.id,
#             qty=1,
#             first_purchase_date=old_date,
#         )
#         db.session.add(cp)
#         db.session.commit()

#         self.assertGreaterEqual(cp.get_holding_period_days(), 400)
#         self.assertTrue(cp.is_long_term_holding())

#     def test_portfolio_allocation(self):
#         """Portfolio allocation percent calculation."""
#         user = self._create_user()
#         entity = self._create_entity()
#         cp = ClientPortfolio(
#             user_id=user.id,
#             entity_id=entity.id,
#             qty=1,
#             current_market_value=200.0,
#         )
#         db.session.add(cp)
#         db.session.commit()

#         pct = cp.calculate_portfolio_allocation(1000.0)
#         self.assertAlmostEqual(pct, 20.0, places=4)
#         self.assertAlmostEqual(cp.portfolio_allocation_percent, 20.0, places=4)

#     def test_calculate_current_values_no_total_invested(self):
#         """current_market_value set, PnL stays None when total_invested is None/0."""
#         user = self._create_user()
#         entity = self._create_entity()
#         for total_invested in (None, 0.0):
#             cp = ClientPortfolio(
#                 user_id=user.id,
#                 entity_id=entity.id,
#                 qty=3,
#                 current_price=50.0,
#                 total_invested=total_invested,
#             )
#             cp.calculate_current_values()
#             db.session.add(cp)
#             db.session.commit()
#             self.assertEqual(cp.current_market_value, 150.0)
#             self.assertIsNone(cp.unrealized_pnl)
#             self.assertIsNone(cp.unrealized_pnl_percent)

#     def test_calculate_current_values_missing_price_or_qty(self):
#         """No calculation when price is None or qty is 0."""
#         user = self._create_user()
#         entity = self._create_entity()

#         cp1 = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=5, current_price=None)
#         cp1.calculate_current_values()
#         db.session.add(cp1)

#         cp2 = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=0, current_price=100.0)
#         cp2.calculate_current_values()
#         db.session.add(cp2)
#         db.session.commit()

#         self.assertIsNone(cp1.current_market_value)
#         self.assertIsNone(cp2.current_market_value)

#     def test_holding_period_defaults_and_not_long_term(self):
#         """No first_purchase_date yields 0 days and not long-term; 200 days is not long-term."""
#         user = self._create_user()
#         entity = self._create_entity()

#         cp_none = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=1)
#         db.session.add(cp_none)
#         db.session.commit()
#         self.assertEqual(cp_none.get_holding_period_days(), 0)
#         self.assertFalse(cp_none.is_long_term_holding())

#         recent_date = datetime.now(timezone.utc) - timedelta(days=200)
#         cp_recent = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=1, first_purchase_date=recent_date)
#         db.session.add(cp_recent)
#         db.session.commit()
#         self.assertFalse(cp_recent.is_long_term_holding())

#     def test_calculate_portfolio_allocation_edge_cases(self):
#         """Allocation returns 0 when no current_market_value or total is 0."""
#         user = self._create_user()
#         entity = self._create_entity()

#         cp_no_mv = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=1)
#         db.session.add(cp_no_mv)
#         db.session.commit()
#         self.assertEqual(cp_no_mv.calculate_portfolio_allocation(1000.0), 0.0)

#         cp_zero_total = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=1, current_market_value=100.0)
#         db.session.add(cp_zero_total)
#         db.session.commit()
#         self.assertEqual(cp_zero_total.calculate_portfolio_allocation(0.0), 0.0)

#     def test_to_dict_nullables(self):
#         """to_dict should serialize None for nullable fields."""
#         user = self._create_user()
#         entity = self._create_entity()

#         cp = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=2)
#         db.session.add(cp)
#         db.session.commit()
#         data = cp.to_dict()
#         self.assertIsNone(data.get('average_cost_basis'))
#         self.assertIsNone(data.get('total_invested'))
#         self.assertIsNone(data.get('current_price'))
#         self.assertIsNone(data.get('current_market_value'))
#         self.assertIsNone(data.get('unrealized_pnl'))
#         self.assertIsNone(data.get('unrealized_pnl_percent'))
#         self.assertIsNone(data.get('first_purchase_date'))
#         self.assertIsNone(data.get('last_transaction_date'))
#         self.assertIsNotNone(data.get('created_at'))
#         self.assertIsNotNone(data.get('updated_at'))

#     def test_updated_at_on_update(self):
#         """updated_at should change when the record is updated."""
#         import time
#         user = self._create_user()
#         entity = self._create_entity()

#         cp = ClientPortfolio(user_id=user.id, entity_id=entity.id, qty=1)
#         db.session.add(cp)
#         db.session.commit()

#         initial_updated_at = cp.updated_at
#         # Ensure time passes to avoid same-timestamp edge cases
#         time.sleep(0.01)
#         cp.qty = 2
#         db.session.commit()

#         self.assertGreaterEqual(cp.updated_at, initial_updated_at)


# if __name__ == '__main__':
#     unittest.main()
