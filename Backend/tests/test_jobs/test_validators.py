import unittest
from datetime import datetime, timedelta
from jobs.validators import (
    validate_ticker,
    validate_sentiment_score,
    validate_url,
    validate_timestamp,
    validate_entity_name,
    validate_news_article,
    validate_sentiment_history,
    validate_batch,
    get_validation_summary,
    sanitize_for_database,
    ValidationResult
)


class TestValidators(unittest.TestCase):

    # -----------------------
    # Ticker validation
    # -----------------------
    def test_validate_ticker_valid(self):
        result = validate_ticker("AAPL")
        self.assertTrue(result)
        self.assertEqual(result.errors, [])

    def test_validate_ticker_invalid_format(self):
        result = validate_ticker("AAP L")
        self.assertFalse(result)
        self.assertIn("Invalid ticker format", result.errors[0])

    def test_validate_ticker_empty(self):
        result = validate_ticker("")
        self.assertFalse(result)
        self.assertIn("Ticker cannot be empty", result.errors[0])

    # -----------------------
    # Sentiment score
    # -----------------------
    def test_validate_sentiment_score_valid(self):
        result = validate_sentiment_score(0.5)
        self.assertTrue(result)
        self.assertEqual(result.errors, [])

    def test_validate_sentiment_score_zero_warning(self):
        result = validate_sentiment_score(0.0)
        self.assertTrue(result)
        self.assertIn("Sentiment score is exactly 0.0", result.warnings[0])

    def test_validate_sentiment_score_invalid_type(self):
        result = validate_sentiment_score("high")
        self.assertFalse(result)
        self.assertIn("must be numeric", result.errors[0])

    # -----------------------
    # URL validation
    # -----------------------
    def test_validate_url_valid(self):
        result = validate_url("https://example.com/news")
        self.assertTrue(result)

    def test_validate_url_invalid_format(self):
        result = validate_url("ftp://bad.url")
        self.assertFalse(result)
        self.assertIn("URL must start with http:// or https://", result.errors[0])

    # -----------------------
    # Timestamp validation
    # -----------------------
    def test_validate_timestamp_valid_datetime(self):
        now = datetime.now()
        result = validate_timestamp(now)
        self.assertTrue(result)

    def test_validate_timestamp_future(self):
        future = datetime.now() + timedelta(hours=2)
        result = validate_timestamp(future)
        self.assertFalse(result)
        self.assertIn("Timestamp is in the future", result.errors[0])

    def test_validate_timestamp_string(self):
        now_str = datetime.now().isoformat()
        result = validate_timestamp(now_str)
        self.assertTrue(result)

    # -----------------------
    # Entity name validation
    # -----------------------
    def test_validate_entity_name_valid(self):
        result = validate_entity_name("Apple Inc")
        self.assertTrue(result)

    def test_validate_entity_name_empty(self):
        result = validate_entity_name("")
        self.assertFalse(result)
        self.assertIn("Entity name cannot be empty", result.errors[0])

    def test_validate_entity_name_special_chars(self):
        result = validate_entity_name("!!!@@@")
        self.assertFalse(result)
        self.assertIn("must contain alphanumeric", result.errors[0])

    # -----------------------
    # Composite news article validation
    # -----------------------
    def test_validate_news_article_valid(self):
        article = {
            "url": "https://example.com/article",
            "ticker": "AAPL",
            "title": "Apple news",
            "published_at": datetime.now(),
            "sentiment_score": 0.5,
            "content": "Some content",
            "source": "TechNews"
        }
        result = validate_news_article(article)
        self.assertTrue(result)

    def test_validate_news_article_missing_field(self):
        article = {
            "url": "https://example.com/article",
            "ticker": "AAPL",
        }
        result = validate_news_article(article)
        self.assertFalse(result)
        self.assertIn("Missing required field", result.errors[0])

    # -----------------------
    # Sentiment history validation
    # -----------------------
    def test_validate_sentiment_history_valid(self):
        data = {
            "ticker": "AAPL",
            "date": datetime.now(),
            "sentiment_score": 0.5,
            "article_count": 5
        }
        result = validate_sentiment_history(data)
        self.assertTrue(result)

    def test_validate_sentiment_history_invalid_article_count(self):
        data = {
            "ticker": "AAPL",
            "date": datetime.now(),
            "sentiment_score": 0.5,
            "article_count": -1
        }
        result = validate_sentiment_history(data)
        self.assertFalse(result)
        self.assertIn("Article count cannot be negative", result.errors[0])

    # -----------------------
    # Validation summary
    # -----------------------
    def test_get_validation_summary(self):
        results = [
            ValidationResult(True, [], []),
            ValidationResult(False, ["error1"], ["warn1"]),
            ValidationResult(True, [], [])
        ]
        summary = get_validation_summary(results)
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['valid'], 2)
        self.assertEqual(summary['invalid'], 1)
        self.assertEqual(summary['total_errors'], 1)
        self.assertEqual(summary['total_warnings'], 1)

    # -----------------------
    # Sanitization
    # -----------------------
    def test_sanitize_for_database(self):
        data = {
            "ticker": "aapl ",
            "title": "Some title   ",
            "content": None,
            "source": "TechNews",
            "extra": 123
        }
        sanitized = sanitize_for_database(data)
        self.assertEqual(sanitized["ticker"], "AAPL")
        self.assertEqual(sanitized["title"], "Some title")
        self.assertNotIn("content", sanitized)
        self.assertEqual(sanitized["extra"], 123)


if __name__ == "__main__":
    unittest.main()
