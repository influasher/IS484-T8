import unittest
from app import create_app, db
from app.models.user import User
import random
import string


class AuthTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up Flask test client and test database"""
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = (
            "postgresql://test_user:test_password@localhost:5432/test_db"
        )
        cls.app.config["JWT_SECRET_KEY"] = "test_secret_key"

        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Drop the database after tests"""
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        """Runs before every test (cleans database)"""
        with self.app.app_context():
            db.session.query(User).delete()
            db.session.commit()

    def tearDown(self):
        """Runs after every test (rollback changes)"""
        with self.app.app_context():
            db.session.rollback()

    def generate_random_string(self, length=8):
        """Generates a random string for test user uniqueness"""
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def test_register_success(self):
        """Test successful user registration"""
        unique_username = "testuser_" + self.generate_random_string()
        unique_email = f"{unique_username}@example.com"

        response = self.client.post(
            "/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["message"], "User created successfully")

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        unique_username1 = "testuser1_" + self.generate_random_string()
        unique_username2 = "testuser2_" + self.generate_random_string()
        unique_email = f"{unique_username1}@example.com"

        self.client.post(
            "/auth/register",
            json={
                "username": unique_username1,
                "email": unique_email,
                "password": "StrongPass123!",
            },
        )

        response = self.client.post(
            "/auth/register",
            json={
                "username": unique_username2,
                "email": unique_email,
                "password": "AnotherPass123!",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["message"], "Email already exists")

    def test_login_success(self):
        """Test successful login"""
        unique_username = "testuser_" + self.generate_random_string()
        unique_email = f"{unique_username}@example.com"

        self.client.post(
            "/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "TestPass123!",
            },
        )
        response = self.client.post(
            "/auth/login", json={"email": unique_email, "password": "TestPass123!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json["data"])

    def test_protected_route_with_token(self):
        """Test accessing protected route with a valid token"""
        unique_username = "testuser_" + self.generate_random_string()
        unique_email = f"{unique_username}@example.com"

        self.client.post(
            "/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "TestPass123!",
            },
        )
        login_response = self.client.post(
            "/auth/login", json={"email": unique_email, "password": "TestPass123!"}
        )
        token = login_response.json["data"]["access_token"]

        response = self.client.get(
            "/auth/protected", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello", response.json["message"])

    def test_logout(self):
        """Test user logout (blacklist JWT token)"""
        unique_username = "testuser_" + self.generate_random_string()
        unique_email = f"{unique_username}@example.com"

        self.client.post(
            "/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "TestPass123!",
            },
        )
        login_response = self.client.post(
            "/auth/login", json={"email": unique_email, "password": "TestPass123!"}
        )
        token = login_response.json["data"]["access_token"]

        response = self.client.post(
            "/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "Logged out successfully")


if __name__ == "__main__":
    unittest.main()
