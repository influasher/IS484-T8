import unittest
import json
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_dir)

from tests.test_config import BaseTestCase
from tests.test_data.user_fixtures import RELATIONSHIP_MANAGERS, JOHN_SMITH_CLIENTS

# Import with error handling
User = None
db = None
try:
    from models.user import User
    from extensions import db
except ImportError:
    pass

class AuthRoutesTestCase(BaseTestCase):
    """Test cases for authentication routes."""
    
    def setUp(self):
        super().setUp()
        if not User:
            self.skipTest("User model not available")
    
    def test_register_success(self):
        """Test successful user registration."""
        test_user = RELATIONSHIP_MANAGERS[0].copy()
        test_user['email'] = 'newuser@example.com'
        test_user['username'] = 'newuser'
        
        response = self.client.post('/api/auth/register', json={
            'email': test_user['email'],
            'username': test_user['username'],
            'password': test_user['password'],
            'full_name': test_user['full_name']
        })
        
        self.assertEqual(response.status_code, 201)
        data = self.get_json_response(response)
        self.assertIn('message', data)
        
        # Verify user was created in database
        user = User.query.filter_by(email=test_user['email']).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, test_user['username'])
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        self.create_test_user()
        
        response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'another_user',
            'password': 'Password123!'
        })
        
        self.assertResponseError(response, 400)
        data = self.get_json_response(response)
        self.assertIn('error', data)
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format."""
        response = self.client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'username': 'testuser',
            'password': 'Password123!'
        })
        
        self.assertResponseError(response, 400)
    
    def test_register_weak_password(self):
        """Test registration with weak password."""
        response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': '123'
        })
        
        self.assertResponseError(response, 400)
    
    def test_login_success(self):
        """Test successful login."""
        self.create_test_user()
        
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        self.assertResponseSuccess(response)
        data = self.get_json_response(response)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'wrong_password'
        })
        
        self.assertResponseError(response, 401)
    
    def test_login_missing_fields(self):
        """Test login with missing required fields."""
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com'
        })
        
        self.assertResponseError(response, 400)
    
    def test_logout(self):
        """Test user logout."""
        user = self.create_test_user()
        headers = self.get_auth_headers()
        
        response = self.client.post('/api/auth/logout', headers=headers)
        
        self.assertResponseSuccess(response)
        data = self.get_json_response(response)
        self.assertIn('message', data)
    
    def test_get_current_user(self):
        """Test getting current user information."""
        user = self.create_test_user()
        headers = self.get_auth_headers()
        
        response = self.client.get('/api/auth/me', headers=headers)
        
        self.assertResponseSuccess(response)
        data = self.get_json_response(response)
        self.assertEqual(data['email'], user.email)
        self.assertEqual(data['username'], user.username)
    
    def test_login_with_test_users(self):
        """Test login with predefined test users."""
        # Test RM login
        rm_data = RELATIONSHIP_MANAGERS[0]
        user = self.create_test_user(rm_data['email'], rm_data['username'])
        
        response = self.client.post('/api/auth/login', json={
            'email': rm_data['email'],
            'password': 'testpassword123'
        })
        
        self.assertResponseSuccess(response)

if __name__ == '__main__':
    unittest.main()
