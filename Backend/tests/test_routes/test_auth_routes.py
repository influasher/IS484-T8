import unittest
from unittest.mock import patch
from app import db
from app.models.user import User
from app.models.user_otp import UserOTP
from tests.integration.setup_mock_db import test_db
import uuid
from flask_jwt_extended import decode_token
from flask_jwt_extended import create_access_token
from app.routes.auth import blacklist 

class AuthIntegrationTest(unittest.TestCase):

    def test_send_otp(self):
        FIXED_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")
        with test_db() as client:
            # create a test user with all NOT NULL fields
            rm = User(
                id=FIXED_UUID,           
                username="tom123",          # must not be None
                email="tom@example.com",
                first_name="Tom",
                last_name="Tim",
                role="RELATIONSHIP_MANAGER",                  
                rm_id=None                    
            )

            c = User(
                id=uuid.uuid4(),             # if id is UUID primary key
                username="alice123",          # must not be None
                email="alice@example.com",
                first_name="Alice",
                last_name="Smith",
                role="CLIENT",                  
                rm_id=FIXED_UUID                    
            )
            
            db.session.add(rm)
            db.session.add(c)
            db.session.commit()

            # Mock the OTP email sending
            with patch("app.services.email_service.EmailService.send_otp_email") as mock_send:
                mock_send.return_value = True  # pretend email sent successfully

                # Call the login endpoint
                response = client.post("/api/auth/login", json={"email": "alice@example.com"})

                # Assert endpoint succeeded
                self.assertEqual(response.status_code, 200)

                # Optional: assert the email sending was called
                mock_send.assert_called_once()

    
    def test_verify_otp(self):
        test_otp_code = "123456"

        with test_db() as client:
            # 1️⃣ Create test user
            user = User(
                id=uuid.uuid4(),           
                username="tom123",          # must not be None
                email="tom@example.com",
                first_name="Tom",
                last_name="Tim",
                role="RELATIONSHIP_MANAGER",                  
                rm_id=None                    
            )
            db.session.add(user)
            db.session.commit()

            # 2️⃣ Create valid OTP record
            otp_record = UserOTP(user_id=user.id, otp_code=test_otp_code)
            db.session.add(otp_record)
            db.session.commit()

            # 3️⃣ Call /verify-otp endpoint
            response = client.post("/api/auth/verify-otp", json={"otp_code": test_otp_code})
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            self.assertIn("access_token", data["data"])
            self.assertEqual(data["data"]["user"]["email"], "tom@example.com")

            # 4️⃣ Assert that OTP is marked as used
            db.session.refresh(otp_record)
            self.assertTrue(otp_record.is_used)

            # 5️⃣ Optional: decode token to verify claims
            token_claims = decode_token(data["data"]["access_token"])
            self.assertEqual(token_claims["sub"], str(user.id))
            self.assertEqual(token_claims["role"], "relationship_manager")

    def test_logout(self):
        with test_db() as client:
            # Create a test user
            user = User(
                id=uuid.uuid4(),           
                username="tom123",          # must not be None
                email="tom@example.com",
                first_name="Tom",
                last_name="Tim",
                role="RELATIONSHIP_MANAGER",                  
                rm_id=None                    
            )
            db.session.add(user)
            db.session.commit()

            # Generate a valid JWT token
            access_token = create_access_token(identity=str(user.id))
            headers = {"Authorization": f"Bearer {access_token}"}

            # Call logout route
            response = client.post("/api/auth/logout", headers=headers)
            self.assertEqual(response.status_code, 200)

            # Decode the token to get the JTI
            decoded = decode_token(access_token)
            jti = decoded["jti"]

            # Ensure the JTI is blacklisted
            self.assertIn(jti, blacklist)

            # Optional: confirm token is actually rejected
            protected_resp = client.get("/api/auth/protected", headers=headers)
            self.assertEqual(protected_resp.status_code, 401)
            self.assertIn("Token has been revoked", protected_resp.get_data(as_text=True))
