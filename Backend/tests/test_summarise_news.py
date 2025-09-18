import os
import unittest
from app.utils.helpers import summarise_news
from dotenv import load_dotenv


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


if __name__ == "__main__":
    unittest.main()
