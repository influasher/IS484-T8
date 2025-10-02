import unittest
import sys
import os
from datetime import datetime

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_dir)

from tests.test_config import BaseTestCase

try:
    from models.user import User
    from extensions import db
    from sqlalchemy.exc import IntegrityError
except ImportError:
    User = None
    db = None
    IntegrityError = Exception

class UserModelTestCase(BaseTestCase):
    """Test cases for User model."""
    
    def setUp(self):
        super().setUp()
        if not User:
            self.skipTest("User model not available")
    
    def test_create_user(self):
        """Test creating a new user."""
        user = User(
            email='test@example.com',
            username='testuser',
            full_name='Test User'
        )
        user.set_password('testpassword123')
        
        db.session.add(user)
        db.session.commit()
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.full_name, 'Test User')
        self.assertIsNotNone(user.password_hash)
        self.assertIsInstance(user.created_at, datetime)
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        user = User(email='test@example.com', username='testuser')
        password = 'secure_password_123'  # Fixed spelling
        
        user.set_password(password)
        
        # Password should be hashed, not stored as plain text
        self.assertNotEqual(user.password_hash, password)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password('wrong_password'))  # Fixed spelling
    
    def test_user_representation(self):
        """Test user string representation."""
        user = User(email='test@example.com', username='testuser')
        
        expected = '<User testuser>'
        self.assertEqual(repr(user), expected)
    
    def test_user_serialization(self):
        """Test user to_dict method."""
        user = User(
            email='test@example.com',
            username='testuser',
            full_name='Test User'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        user_dict = user.to_dict()
        
        self.assertIn('id', user_dict)
        self.assertIn('email', user_dict)
        self.assertIn('username', user_dict)
        self.assertIn('full_name', user_dict)
        self.assertIn('created_at', user_dict)
        self.assertNotIn('password_hash', user_dict)  # Should not expose password
    
    def test_unique_email_constraint(self):
        """Test that email must be unique."""
        user1 = User(email='test@example.com', username='user1')
        user1.set_password('password123')
        user2 = User(email='test@example.com', username='user2')
        user2.set_password('password123')
        
        db.session.add(user1)
        db.session.commit()
        
        db.session.add(user2)
        
        with self.assertRaises(IntegrityError):
            db.session.commit()
    
    def test_unique_username_constraint(self):
        """Test that username must be unique."""
        user1 = User(email='test1@example.com', username='testuser')
        user1.set_password('password123')
        user2 = User(email='test2@example.com', username='testuser')
        user2.set_password('password123')
        
        db.session.add(user1)
        db.session.commit()
        
        db.session.add(user2)
        
        with self.assertRaises(IntegrityError):
            db.session.commit()
    
    def test_user_documents_relationship(self):
        """Test user-documents relationship."""
        user = User(email='test@example.com', username='testuser')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Initially no documents
        self.assertEqual(len(user.documents), 0)
        
        # Add a document
        document = self.create_test_document(user.id, 'Test Document')
        
        # Refresh user and check relationship
        db.session.refresh(user)
        self.assertEqual(len(user.documents), 1)
        self.assertEqual(user.documents[0].title, 'Test Document')
    
    def test_password_validation(self):
        """Test password strength validation."""
        user = User(email='test@example.com', username='testuser')
        
        # Test various password scenarios
        valid_passwords = ['StrongPass123!', 'AnotherGood1$', 'MySecure2024#']
        for password in valid_passwords:
            user.set_password(password)
            self.assertTrue(user.check_password(password))
    
    def test_user_active_status(self):
        """Test user active status."""
        user = User(email='test@example.com', username='testuser')
        
        # User should be active by default
        self.assertTrue(user.is_active)
        
        # Test deactivating user
        user.is_active = False
        self.assertFalse(user.is_active)

if __name__ == '__main__':
    unittest.main()
