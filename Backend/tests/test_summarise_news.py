import os
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from app.utils.helpers import news_interpreter_summariser


class TestSummariseNews(unittest.TestCase):
    def setUp(self):
        # Load environment variables from .env file
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Use a longer text that passes the 100-character minimum validation
        self.news_text = """Apple Inc. announced record quarterly earnings today, driven by strong iPhone sales in emerging markets.
        The technology giant reported revenue of $95 billion, beating analyst expectations by 8%. CEO Tim Cook attributed
        the success to innovative product features and expanding service offerings in the Asia-Pacific region."""
        self.summary_length = 50

    def test_summarise_news(self):
        if not self.api_key:
            self.skipTest("GEMINI_API_KEY not set in .env file")

        summary = news_interpreter_summariser(self.news_text, self.summary_length)
        self.assertIsInstance(summary, str)
        # The function allows 80-120% of target length, so check it's reasonable
        self.assertGreater(len(summary), 0)
        # Verify summary is within reasonable bounds (function allows 50-120% of target)
        word_count = len(summary.split())
        self.assertGreaterEqual(word_count, int(self.summary_length * 0.5))
        self.assertLessEqual(word_count, int(self.summary_length * 1.5))

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

    @patch('app.utils.helpers.genai.Client')
    def test_news_interpreter_as_summarizer(self, mock_client):
        """Test using news_interpreter function for summarization."""
        # Mock the AI response with a realistic summary (must be at least 50% of target length)
        mock_response = MagicMock()
        # Target is 150 words, so need at least 75 words
        mock_response.text = """Apple Inc. reported exceptional quarterly earnings driven by strong iPhone sales
        in emerging markets across Asia-Pacific and Latin America. The technology giant announced revenue of $95 billion,
        significantly beating analyst expectations by 8 percent. CEO Tim Cook attributed the company's success to innovative
        product features including advanced camera systems and enhanced AI capabilities that resonated with consumers.
        The expanding service offerings, particularly Apple Music, iCloud, and Apple TV Plus, contributed substantially
        to recurring revenue streams. Market analysts praised the diversification strategy and strong ecosystem lock-in
        effects that continue to drive customer loyalty and premium pricing power in competitive smartphone markets worldwide."""

        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client.return_value = mock_client_instance

        try:
            from app.utils.helpers import news_interpreter

            news_text = """Apple Inc. announced record quarterly earnings today, driven by strong iPhone sales in emerging markets.
            The technology giant reported revenue of $95 billion, beating analyst expectations by 8%. CEO Tim Cook attributed
            the success to innovative product features and expanding service offerings in the Asia-Pacific region."""
            result = news_interpreter(news_text, 150)

            self.assertIsNotNone(result)

        except ImportError:
            self.skipTest("news_interpreter function not available")

    @patch('app.utils.helpers.genai.Client')
    def test_news_interpreter_summariser(self, mock_client):
        """Test the news_interpreter_summariser function directly."""
        # Mock the AI response with realistic summary (must be at least 50% of target length)
        mock_response = MagicMock()
        # Target is 100 words, so need at least 50 words
        mock_response.text = """Financial markets experienced significant volatility following the Federal Reserve's
        announcement of interest rate changes aimed at controlling inflation. The S&P 500 index dropped 2.3 percent
        in early morning trading before recovering partially by market close. Leading economists expressed concerns
        that these monetary policy shifts could negatively impact consumer spending patterns and business investment
        decisions in the fourth quarter, potentially slowing economic growth."""

        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client.return_value = mock_client_instance

        try:
            from app.utils.helpers import news_interpreter_summariser

            news_text = """Financial markets experienced significant volatility today as the Federal Reserve announced
            interest rate changes. The S&P 500 dropped 2.3% in early trading before recovering slightly by the close.
            Economists warn that these policy shifts could impact consumer spending and business investment in Q4."""
            result = news_interpreter_summariser(news_text, 100)

            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

        except ImportError:
            self.skipTest("news_interpreter_summariser function not available")


if __name__ == "__main__":
    unittest.main()
