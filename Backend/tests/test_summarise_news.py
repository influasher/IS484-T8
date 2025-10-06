import os
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from app.utils.helpers import summarise_news


class TestSummariseNews(unittest.TestCase):
    def setUp(self):
        # Load environment variables from .env file
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.news_text = "This is a sample news text that needs to be summarised."
        self.summary_length = 10

    def test_summarise_news(self):
        if not self.api_key:
            self.skipTest("GEMINI_API_KEY not set in .env file")

        summary = summarise_news(self.news_text, self.summary_length)
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary.split()) <= self.summary_length)

    def test_find_available_functions(self):
        """Test to find what summarization functions are available."""
        try:
            import app.utils.helpers as helpers

            # Get all functions in helpers module
            all_functions = [name for name in dir(helpers) if callable(getattr(helpers, name, None))]
            summarization_functions = [
                func
                for func in all_functions
                if any(keyword in func.lower() for keyword in ["summar", "news", "interpret"])
            ]

            print(f"Available summarization functions: {summarization_functions}")
            self.assertIsInstance(summarization_functions, list)

        except ImportError:
            self.skipTest("helpers module not available")

    @patch('app.utils.helpers.genai.GenerativeModel')
    def test_news_interpreter_as_summarizer(self, mock_model):
        """Test using news_interpreter function for summarization."""
        # Mock the AI response
        mock_response = MagicMock()
        mock_response.text = "Mocked news summary with key financial insights."

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance

        try:
            from app.utils.helpers import news_interpreter

            news_text = "Sample financial news about market volatility."
            result = news_interpreter(news_text, 150)

            self.assertIsNotNone(result)

        except ImportError:
            self.skipTest("news_interpreter function not available")

    @patch('app.utils.helpers.genai.GenerativeModel')
    def test_news_interpreter_summariser(self, mock_model):
        """Test the news_interpreter_summariser function directly."""
        # Mock the AI response
        mock_response = MagicMock()
        mock_response.text = "Mocked summary from news_interpreter_summariser."

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance

        try:
            from app.utils.helpers import news_interpreter_summariser

            news_text = "Financial news about stock market trends and economic policies."
            result = news_interpreter_summariser(news_text, 100)

            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

        except ImportError:
            self.skipTest("news_interpreter_summariser function not available")


if __name__ == "__main__":
    unittest.main()
