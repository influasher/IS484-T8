import unittest
import tempfile
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Import conftest to ensure proper path setup
try:
    from . import conftest
    BACKEND_AVAILABLE = conftest.BACKEND_MODULES_AVAILABLE
except ImportError:
    BACKEND_AVAILABLE = False

# Import backend modules with comprehensive error handling
create_app = None
db = None

if BACKEND_AVAILABLE:
    try:
        from app import create_app
        print("Successfully imported create_app")
    except ImportError as e:
        print(f"Warning: Could not import create_app from app module: {e}")
        
    # Try multiple paths for extensions
    try:
        from extensions import db
        print("Successfully imported db from extensions")
    except ImportError:
        try:
            from app.extensions import db
            print("Successfully imported db from app.extensions")
        except ImportError:
            try:
                from app.models import db
                print("Successfully imported db from app.models")
            except ImportError as e:
                print(f"Warning: Could not import db from any extensions module: {e}")

class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and teardown."""
    
    def setUp(self):
        """Set up test client and database."""
        if not create_app or not db:
            self.skipTest("Core backend modules (app, extensions) not available")
            
        # Create temporary database file - NEVER touches live DB
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='_test.db')
        
        # Configure app for testing with ISOLATED test database
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.db_path}',  # ISOLATED test DB
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key-NOT-FOR-PRODUCTION',
            'WTF_CSRF_ENABLED': False,
            'JWT_SECRET_KEY': 'test-jwt-secret-NOT-FOR-PRODUCTION',
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'isolation_level': 'AUTOCOMMIT'
            },
            # Ensure we NEVER use production database
            'DATABASE_URL': f'sqlite:///{self.db_path}',
            'ENV': 'testing'
        }
        
        # Double-check we're not using production database
        if 'postgres' in test_config.get('SQLALCHEMY_DATABASE_URI', '').lower():
            raise ValueError("CRITICAL: Test trying to use production PostgreSQL database!")
        
        self.app = create_app(test_config)
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables with proper transaction handling
        with self.app.app_context():
            try:
                db.create_all()
                db.session.commit()
            except Exception as e:
                print(f"Warning: Error creating tables: {e}")
    
    def tearDown(self):
        """Clean up ONLY test database - never touches live DB."""
        if hasattr(self, 'app_context') and db:
            try:
                # Only cleanup our isolated test database
                db.session.rollback()
                db.session.remove()
                
                # For test SQLite database only
                if hasattr(self, 'db_path') and self.db_path:
                    db.drop_all()  # Only drops tables in test DB
                    
            except Exception as e:
                print(f"Warning: Error during test cleanup: {e}")
            finally:
                self.app_context.pop()
                # Delete temporary test database file
                if hasattr(self, 'db_fd') and hasattr(self, 'db_path'):
                    try:
                        os.close(self.db_fd)
                        os.unlink(self.db_path)  # Delete test DB file
                    except Exception:
                        pass
    
    def create_test_user(self, email="test@example.com", username="testuser"):
        """Helper method to create test user."""
        User = None
        try:
            from models.user import User
        except ImportError:
            self.skipTest("User model not available")
            
        user = User(email=email, username=username)
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()
        return user
    
    def login_user(self, email="test@example.com", password="testpassword123"):
        """Helper method to login user and return response."""
        return self.client.post('/api/auth/login', json={
            'email': email,
            'password': password
        })
    
    def create_test_document(self, user_id=None, title="Test Document"):
        """Helper method to create test document."""
        Document = None
        try:
            from models.document import Document
        except ImportError:
            self.skipTest("Document model not available")
        
        if user_id is None:
            user_id = self.user.id if hasattr(self, 'user') else self.create_test_user().id
        
        document = Document(
            title=title,
            filename="test.pdf",
            file_path="/test/path/test.pdf",
            file_size=1024,
            content="Test document content for analysis and processing",
            user_id=user_id
        )
        db.session.add(document)
        db.session.commit()
        return document
    
    def get_auth_headers(self, user_email="test@example.com", password="testpassword123"):
        """Get authorization headers for authenticated requests."""
        if not hasattr(self, '_auth_token'):
            login_response = self.login_user(user_email, password)
            if login_response.status_code == 200:
                data = json.loads(login_response.data)
                self._auth_token = data.get('access_token')
        
        return {'Authorization': f'Bearer {self._auth_token}'} if self._auth_token else {}
    
    def assertResponseSuccess(self, response):
        """Assert that response is successful (2xx)."""
        self.assertGreaterEqual(response.status_code, 200)
        self.assertLess(response.status_code, 300)
    
    def assertResponseError(self, response, expected_code=None):
        """Assert that response is an error (4xx or 5xx)."""
        if expected_code:
            self.assertEqual(response.status_code, expected_code)
        else:
            self.assertGreaterEqual(response.status_code, 400)
    
    def get_json_response(self, response):
        """Get JSON data from response."""
        return json.loads(response.data.decode('utf-8'))
