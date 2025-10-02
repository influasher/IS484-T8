import unittest
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

class MinimalFunctionalityTestCase(unittest.TestCase):
    """Minimal tests that always work to verify test framework."""
    
    def test_basic_python_functionality(self):
        """Test basic Python functionality."""
        self.assertEqual(2 + 2, 4)
        self.assertTrue(True)
        self.assertFalse(False)
    
    def test_string_operations(self):
        """Test string operations."""
        test_string = "Hello, World!"
        self.assertIn("Hello", test_string)
        self.assertEqual(len(test_string), 13)
        self.assertTrue(test_string.startswith("Hello"))
    
    def test_list_operations(self):
        """Test list operations."""
        test_list = [1, 2, 3, 4, 5]
        self.assertEqual(len(test_list), 5)
        self.assertIn(3, test_list)
        self.assertEqual(test_list[0], 1)
    
    def test_dictionary_operations(self):
        """Test dictionary operations."""
        test_dict = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(test_dict['key1'], 'value1')
        self.assertIn('key2', test_dict)
        self.assertEqual(len(test_dict), 2)
    
    def test_import_capability(self):
        """Test that we can import standard libraries."""
        import json
        import datetime
        import uuid
        
        # Test JSON functionality
        data = {'test': 'data'}
        json_string = json.dumps(data)
        parsed_data = json.loads(json_string)
        self.assertEqual(parsed_data['test'], 'data')
        
        # Test datetime functionality
        now = datetime.datetime.now()
        self.assertIsInstance(now, datetime.datetime)
        
        # Test UUID functionality
        test_uuid = uuid.uuid4()
        self.assertIsInstance(test_uuid, uuid.UUID)

if __name__ == '__main__':
    unittest.main()
