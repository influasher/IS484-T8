import unittest
from unittest.mock import patch
from app import db
from tests.test_routes.setup_mock_db import test_db
import uuid
from app.models.user import User, UserRole
from app.models import ClientPreferences
from flask_jwt_extended import create_access_token
from datetime import datetime


class UserIntegrationTest(unittest.TestCase):
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

        client_user = User(
            id=self.client_id,             # if id is UUID primary key
            username="client_user",          # must not be None
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
            role="CLIENT",                  
            rm_id=self.rm_id                    
        )

        db.session.add(rm)
        db.session.add(client_user)
        db.session.commit()

        self.rm_token = create_access_token(identity=str(rm.id))
        self.client_token = create_access_token(identity=str(client_user.id))

    def test_create_client(self):
        with test_db() as client:
            self._create_sample_data()
            fixed_time = datetime(2025, 10, 31, 12, 0, 0)
            payload = {
                "username": "new_client",
                "email": "new_client@example.com",
                "first_name": "New",
                "last_name": "Client",
                "holding": 1000,
                "overall_pl": 50.5,
                "risk_cap": "Moderate",
                "sectors": ["Tech", "Finance"],
                
            }
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value = fixed_time
                response = client.post(
                    "/api/user/create-clients",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.rm_token}"},
                )
                data = response.get_json()
                self.assertEqual(response.status_code, 200)
                self.assertIn("CLIENT and preferences created successfully", data["message"])
                self.assertEqual(data["data"]["user"]["username"], "new_client")
                self.assertEqual(data["data"]["preferences"]["holding"], 1000)

    def test_get_clients(self):
        with test_db() as client:
            self._create_sample_data()
            response = client.get(
                "/api/user/clients",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertIn("Clients fetched successfully", data["message"])
            self.assertGreaterEqual(len(data["data"]), 1)
            self.assertEqual(data["data"][0]["id"], str(self.client_id))

    def test_get_user_by_id_as_rm(self):
        with test_db() as client:
            self._create_sample_data()
            response = client.get(
                f"/api/user/{self.client_id}",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["data"]["username"], "client_user")

    def test_get_user_by_id_as_client_self(self):
        with test_db() as client:
            self._create_sample_data()
            response = client.get(
                f"/api/user/{self.client_id}",
                headers={"Authorization": f"Bearer {self.client_token}"}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["data"]["username"], "client_user")

    def test_get_user_by_id_access_denied(self):
        with test_db() as client:
            self._create_sample_data()
            # Client trying to access another client
            other_client_id = uuid.uuid4()
            other_client = User(
                id=other_client_id,
                username="other_client",
                email="other@example.com",
                first_name="Other",
                last_name="Client",
                role=UserRole.CLIENT
            )
            db.session.add(other_client)
            db.session.commit()

            response = client.get(
                f"/api/user/{other_client_id}",
                headers={"Authorization": f"Bearer {self.client_token}"}
            )
            self.assertEqual(response.status_code, 403)

    def test_update_client_preferences(self):
        with test_db() as client:
            self._create_sample_data()
            payload = {"holding": 2000, "overall_pl": 100.5, "risk_cap": "High"}
            response = client.put(
                f"/api/user/{self.client_id}/preferences",
                json=payload,
                headers={"Authorization": f"Bearer {self.rm_token}"},
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["data"]["holding"], 2000)
            self.assertEqual(data["data"]["overall_pl"], 100.5)
            self.assertEqual(data["data"]["risk_cap"], "High")

    def test_get_client_preferences(self):
        with test_db() as client:
            self._create_sample_data()
            response = client.get(
                f"/api/user/{self.client_id}/preferences",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["data"]["holding"], 0.0)  # Default applied if empty

