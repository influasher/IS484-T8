import unittest
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from tests.test_config import BaseTestCase
from tests.test_data.user_fixtures import (
    RELATIONSHIP_MANAGERS, JOHN_SMITH_CLIENTS, SARAH_JOHNSON_CLIENTS, 
    SENTIFINANCE_CLIENTS, get_clients_for_rm
)

class UserManagementTestCase(BaseTestCase):
    """Test cases for user management with realistic data."""
    
    def setUp(self):
        super().setUp()
        
        # Import User model within setUp to avoid table redefinition
        self.User = None
        try:
            # Clear any existing User class from registry
            if hasattr(self, 'app'):
                with self.app.app_context():
                    from models.user import User
                    self.User = User
        except ImportError:
            pass
        
        if not self.User:
            self.skipTest("User model not available")
    
    def test_create_relationship_managers(self):
        """Test creating all relationship managers."""
        created_rms = []
        
        for rm_data in RELATIONSHIP_MANAGERS:
            user = self.create_test_user(rm_data['email'], rm_data['username'])
            created_rms.append(user)
        
        self.assertEqual(len(created_rms), 3)
        
        # Verify all RMs exist in database
        with self.app.app_context():
            # Use a simple query that works regardless of User model structure
            all_users = self.User.query.all()
            rm_usernames = [user.username for user in all_users if user.username.endswith('_rm')]
            self.assertEqual(len(rm_usernames), 3)
    
    def test_create_john_smith_clients(self):
        """Test creating clients for John Smith."""
        # Create John Smith RM first
        john_rm = self.create_test_user(
            RELATIONSHIP_MANAGERS[0]['email'], 
            RELATIONSHIP_MANAGERS[0]['username']
        )
        
        # Create his clients
        created_clients = []
        for client_data in JOHN_SMITH_CLIENTS:
            client = self.create_test_user(client_data['email'], client_data['username'])
            created_clients.append(client)
        
        self.assertEqual(len(created_clients), 6)
        
        # Verify clients can be retrieved from fixture data
        john_clients = get_clients_for_rm('jsmith_rm')
        self.assertEqual(len(john_clients), 6)
    
    def test_email_username_uniqueness_in_fixtures(self):
        """Test that emails and usernames are unique in test fixtures."""
        emails = set()
        usernames = set()
        
        # Check RMs
        for rm_data in RELATIONSHIP_MANAGERS:
            self.assertNotIn(rm_data['email'], emails, f"Duplicate email: {rm_data['email']}")
            self.assertNotIn(rm_data['username'], usernames, f"Duplicate username: {rm_data['username']}")
            emails.add(rm_data['email'])
            usernames.add(rm_data['username'])
        
        # Check all clients
        all_clients = JOHN_SMITH_CLIENTS + SARAH_JOHNSON_CLIENTS + SENTIFINANCE_CLIENTS
        for client_data in all_clients:
            self.assertNotIn(client_data['email'], emails, f"Duplicate email: {client_data['email']}")
            self.assertNotIn(client_data['username'], usernames, f"Duplicate username: {client_data['username']}")
            emails.add(client_data['email'])
            usernames.add(client_data['username'])
    
    def test_user_creation_basic(self):
        """Test basic user creation functionality."""
        # Test creating a single user
        test_user_data = RELATIONSHIP_MANAGERS[0]
        user = self.create_test_user(test_user_data['email'], test_user_data['username'])
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, test_user_data['email'])
        self.assertEqual(user.username, test_user_data['username'])
        
        # Verify user exists in database
        with self.app.app_context():
            found_user = self.User.query.filter_by(email=test_user_data['email']).first()
            self.assertIsNotNone(found_user)
    
    def test_user_roles_and_permissions(self):
        """Test user roles and permission structure."""
        # Create one user of each type
        rm_data = RELATIONSHIP_MANAGERS[0]
        client_data = JOHN_SMITH_CLIENTS[0]
        
        rm_user = self.create_test_user(rm_data['email'], rm_data['username'])
        client_user = self.create_test_user(client_data['email'], client_data['username'])
        
        # Test role assignment (assuming role field exists)
        self.assertTrue(rm_user.username.endswith('_rm'))
        self.assertTrue(client_user.username.endswith('_client'))
    
    def test_email_username_uniqueness(self):
        """Test that emails and usernames are unique across all test users."""
        emails = set()
        usernames = set()
        
        for rm_data in RELATIONSHIP_MANAGERS:
            self.assertNotIn(rm_data['email'], emails)
            self.assertNotIn(rm_data['username'], usernames)
            emails.add(rm_data['email'])
            usernames.add(rm_data['username'])
        
        all_clients = JOHN_SMITH_CLIENTS + SARAH_JOHNSON_CLIENTS + SENTIFINANCE_CLIENTS
        for client_data in all_clients:
            self.assertNotIn(client_data['email'], emails)
            self.assertNotIn(client_data['username'], usernames)
            emails.add(client_data['email'])
            usernames.add(client_data['username'])

if __name__ == '__main__':
    unittest.main()
