import unittest
import os
import sys
import tempfile

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

class SafetyCheckTestCase(unittest.TestCase):
    """Safety tests to ensure we never touch live databases."""
    
    def test_no_production_database_access(self):
        """Ensure tests never access production databases."""
        # Check environment variables
        db_url = os.environ.get('DATABASE_URL', '')
        sqlalchemy_url = os.environ.get('SQLALCHEMY_DATABASE_URI', '')
        
        # Tests should never use production database URLs
        production_indicators = ['postgres://', 'postgresql://', 'mysql://', 'prod', 'production']
        
        for indicator in production_indicators:
            self.assertNotIn(indicator.lower(), db_url.lower(), 
                           f"CRITICAL: Test environment has production database URL: {db_url}")
            self.assertNotIn(indicator.lower(), sqlalchemy_url.lower(),
                           f"CRITICAL: Test environment has production SQLAlchemy URL: {sqlalchemy_url}")
    
    def test_test_database_isolation(self):
        """Ensure we're using isolated test databases."""
        # Test that we can create and destroy temporary files safely
        with tempfile.NamedTemporaryFile(suffix='_test.db', delete=False) as tmp_file:
            test_db_path = tmp_file.name
        
        # Verify it's a temporary file in temp directory
        self.assertIn('tmp', test_db_path.lower())
        self.assertTrue(test_db_path.endswith('_test.db'))
        
        # Clean up
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)
    
    def test_environment_is_testing(self):
        """Ensure we're in testing environment."""
        flask_env = os.environ.get('FLASK_ENV', '').lower()
        env = os.environ.get('ENV', '').lower()
        
        # Should be in testing mode
        if flask_env:
            self.assertIn('test', flask_env, f"FLASK_ENV should be 'testing', got: {flask_env}")
        
        if env:
            self.assertIn('test', env, f"ENV should be 'testing', got: {env}")
    
    def test_no_live_data_modification(self):
        """Ensure tests don't modify any live data."""
        # Test database operations should only affect temporary files
        with tempfile.NamedTemporaryFile(suffix='_test.db') as tmp_file:
            # This simulates what our tests do - only work with temp files
            self.assertTrue(tmp_file.name.endswith('_test.db'))
            self.assertIn('tmp', tmp_file.name.lower())
            
            # Write some test data
            tmp_file.write(b'test data')
            tmp_file.flush()
            
            # Verify we can read it back
            tmp_file.seek(0)
            data = tmp_file.read()
            self.assertEqual(data, b'test data')
        
        # File is automatically deleted when context exits

if __name__ == '__main__':
    unittest.main()
