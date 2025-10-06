from app.utils.helpers import news_interpreter
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from tests.test_config import BaseTestCase

class NewsInterpreterTestCase(BaseTestCase):
    """Test cases for news interpreter functionality."""
    
    @patch('app.utils.helpers.genai.GenerativeModel')
    def test_news_interpreter_mocked(self, mock_model):
        """Test news interpreter with mocked AI model."""
        # Mock the AI response
        mock_response = MagicMock()
        mock_response.text = "This is a mocked news summary with key insights."
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        try:
            from app.utils.helpers import news_interpreter
            
            news_text = "Sample news article about market trends and economic indicators."
            result = news_interpreter(news_text, 100)
            
            self.assertIsNotNone(result)
            
        except ImportError:
            self.skipTest("news_interpreter function not available")
        except Exception as e:
            # Expected behavior when API key is invalid
            self.assertIn("API key", str(e).lower())

    def test_news_interpreter_without_api_key(self):
        """Test news interpreter behavior without valid API key."""
        try:
            from app.utils.helpers import news_interpreter
            
            # This should handle the missing/invalid API key gracefully
            with patch.dict(os.environ, {}, clear=True):
                news_text = "Sample news article"
                result = news_interpreter(news_text, 100)
                
                # Should return some fallback response or handle the error
                self.assertIsNotNone(result)
                
        except ImportError:
            self.skipTest("news_interpreter function not available")
        except Exception as e:
            # Expected behavior when API key is invalid
            self.assertIn("API key", str(e).lower())

if __name__ == '__main__':
    unittest.main()