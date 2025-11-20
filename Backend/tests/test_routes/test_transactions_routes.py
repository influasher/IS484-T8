import unittest
from app import db
from tests.test_routes.setup_mock_db import test_db
from app.models.user import User
from app.models.entity import Entity
from app.models.transactions import Transactions, TransactionType, Currency
import uuid
from flask_jwt_extended import create_access_token

class TransactionsIntegrationTest(unittest.TestCase):
    def _create_sample_data(self):
        # Create a sample client
        self.client_id = uuid.uuid4()
        self.rm_id = uuid.uuid4()
        rm = User(
            id=self.rm_id,           
            username="tom123",          # must not be None
            email="tom@example.com",
            first_name="Tom",
            last_name="Tim",
            role="RELATIONSHIP_MANAGER",                  
            rm_id=None                    
        )

        c = User(
            id=self.client_id,             # if id is UUID primary key
            username="alice123",          # must not be None
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
            role="CLIENT",                  
            rm_id=self.rm_id                    
        )

        entity = Entity(
            id=uuid.uuid4(),
            name="Apple",
            ticker="AAPL"
        )

        db.session.add(entity)
        db.session.add(rm)
        db.session.add(c)
        db.session.commit()

        # Generate a valid JWT token
        self.access_token = create_access_token(identity=str(rm.id))

    def test_add_transaction_success(self):
        """Test creating a new DEPOSIT transaction"""
        with test_db() as client:
            self._create_sample_data()
            payload = {
                "client_uuid": str(self.client_id),
                "type": "DEPOSIT",
                "amount": 1000,
                "currency": "USD",
                "source": "Bank",
                "desc": "Initial deposit"
            }

            response = client.post("/api/transactions/add_transaction",
                                        json=payload, headers={"Authorization": f"Bearer {self.access_token}"})
            data = response.get_json()

            self.assertEqual(response.status_code, 201)
            self.assertIn("Transaction created successfully", data["message"])
            self.assertEqual(float(data["transaction"]["amount"]), 1000)
            self.assertEqual(data["transaction"]["type"], "DEPOSIT")

    def test_add_stock_transaction_success(self):
        """Test creating a BUY stock transaction"""
        with test_db() as client:
            self._create_sample_data()
            payload = {
                "client_uuid": str(self.client_id),
                "type": "BUY",
                "source": "AAPL",
                "qty": 5
            }

            response = client.post("/api/transactions/add_transaction",
                                        json=payload, headers={"Authorization": f"Bearer {self.access_token}"})
            data = response.get_json()
            print(data)

            self.assertEqual(response.status_code, 201)
            self.assertEqual(data["transaction"]["type"], "BUY")
            self.assertEqual(data["transaction"]["source"], "AAPL")
            self.assertEqual(data["transaction"]["txn_uuid"], str(data["transaction"]["txn_uuid"]))
            self.assertGreater(data["transaction"]["amount"], 0)

    def test_get_all_transactions(self):
        """Test fetching all transactions"""
        with test_db() as client:
            self._create_sample_data()
            txn = Transactions(
                txn_uuid=uuid.uuid4(),
                client_uuid=self.client_id,
                type=TransactionType.DEPOSIT,
                source="Bank",
                currency=Currency.USD,
                amount=500
            )
            db.session.add(txn)
            db.session.commit()

            response = client.get("/api/transactions/", headers={"Authorization": f"Bearer {self.access_token}"})
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["count"], 1)
            self.assertEqual(float(data["transactions"][0]["amount"]), 500)

    def test_get_transactions_by_client_param(self):
        """Test fetching transactions for a specific client via URL param"""
        with test_db() as client:
            self._create_sample_data()
            txn = Transactions(
                txn_uuid=uuid.uuid4(),
                client_uuid=self.client_id,
                type=TransactionType.DEPOSIT,
                source="Bank",
                currency=Currency.USD,
                amount=750
            )
            db.session.add(txn)
            db.session.commit()

            response = client.get(f"/api/transactions/client/{self.client_id}", headers={"Authorization": f"Bearer {self.access_token}"})
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["client_id"], str(self.client_id))
            self.assertEqual(data["count"], 1)
            self.assertEqual(float(data["transactions"][0]["amount"]), 750)

    def test_get_transactions_missing_client(self):
        """Test 404 when client does not exist"""
        with test_db() as client:
            self._create_sample_data()
            fake_client_id = uuid.uuid4()
            response = client.get(f"/api/transactions/client/{fake_client_id}", headers={"Authorization": f"Bearer {self.access_token}"})
            self.assertEqual(response.status_code, 404)
            self.assertIn("Client not found", response.get_json()["error"])
