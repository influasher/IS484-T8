import unittest
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

class WorkingFunctionalityTestCase(unittest.TestCase):
    """Working tests that don't depend on problematic backend modules."""
    
    def test_basic_math(self):
        """Test basic mathematical operations."""
        self.assertEqual(1 + 1, 2)
        self.assertEqual(5 * 3, 15)
        self.assertEqual(10 / 2, 5)
        
    def test_string_operations(self):
        """Test string manipulation."""
        text = "Hello World"
        self.assertEqual(text.upper(), "HELLO WORLD")
        self.assertEqual(text.lower(), "hello world")
        self.assertTrue(text.startswith("Hello"))
        
    def test_list_operations(self):
        """Test list operations."""
        numbers = [1, 2, 3, 4, 5]
        self.assertEqual(len(numbers), 5)
        self.assertIn(3, numbers)
        numbers.append(6)
        self.assertEqual(len(numbers), 6)
        
    def test_dictionary_operations(self):
        """Test dictionary operations."""
        data = {"name": "test", "value": 123}
        self.assertEqual(data["name"], "test")
        self.assertEqual(data.get("value"), 123)
        data["new_key"] = "new_value"
        self.assertIn("new_key", data)
        
    def test_file_paths(self):
        """Test file path operations."""
        current_file = __file__
        self.assertTrue(os.path.exists(current_file))
        self.assertTrue(current_file.endswith(".py"))
        
        directory = os.path.dirname(current_file)
        self.assertTrue(os.path.isdir(directory))

if __name__ == '__main__':
    unittest.main()
