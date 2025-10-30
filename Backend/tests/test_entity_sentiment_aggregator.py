import unittest
from types import SimpleNamespace
from datetime import datetime, timedelta

try:
    from app.services import entity_sentiment_aggregator as mod
except Exception:
    import entity_sentiment_aggregator as mod  # fallback


# Mock News article for testing
class MockNews:
    def __init__(self, score=0.0, confidence=0.7, published_date=None, title="Test Article", url="http://test.com"):
        self.score = score
        self.confidence = confidence
        self.published_date = published_date or datetime.utcnow()
        self.finbert_score = score * 0.8  # Mock finbert score
        self.second_model_score = score * 0.9  # Mock second model score
        self.third_model_score = score * 1.1  # Mock third model score
        self.title = title
        self.url = url


class EntitySentimentAggregatorTests(unittest.TestCase):

    def setUp(self):
        self.aggregator = mod.EntitySentimentAggregator(lookback_days=30)

    def test_aggregator_initialization(self):
        """Test that aggregator initializes with correct lookback days"""
        aggregator = mod.EntitySentimentAggregator(lookback_days=15)
        self.assertEqual(aggregator.lookback_days, 15)

        # Test default initialization
        default_aggregator = mod.EntitySentimentAggregator()
        self.assertEqual(default_aggregator.lookback_days, 30)

    def test_calculate_weighted_sentiment_empty_articles(self):
        """Test sentiment calculation with no articles returns default values"""
        result = self.aggregator.calculate_weighted_sentiment([])

        expected_keys = [
            'sentiment_score', 'simple_average', 'confidence_weighted',
            'time_decay', 'combined_weighted', 'finbert_average',
            'classification', 'confidence_score', 'article_count'
        ]

        for key in expected_keys:
            self.assertIn(key, result)

        self.assertEqual(result['sentiment_score'], 0.0)
        self.assertEqual(result['classification'], 'neutral')
        self.assertEqual(result['article_count'], 0)

    def test_calculate_weighted_sentiment_single_article(self):
        """Test sentiment calculation with single article"""
        articles = [MockNews(score=25.0, confidence=0.8)]
        result = self.aggregator.calculate_weighted_sentiment(articles)

        self.assertEqual(result['sentiment_score'], 25.0)
        self.assertEqual(result['simple_average'], 25.0)
        self.assertEqual(result['confidence_weighted'], 25.0)
        self.assertEqual(result['classification'], 'bullish')
        self.assertEqual(result['article_count'], 1)

    def test_calculate_weighted_sentiment_multiple_articles(self):
        """Test sentiment calculation with multiple articles"""
        articles = [
            MockNews(score=20.0, confidence=0.9),
            MockNews(score=-10.0, confidence=0.7),
            MockNews(score=5.0, confidence=0.8)
        ]
        result = self.aggregator.calculate_weighted_sentiment(articles)

        # Simple average should be (20 - 10 + 5) / 3 = 5.0
        self.assertEqual(result['simple_average'], 5.0)
        self.assertEqual(result['article_count'], 3)

        # Confidence weighted should favor higher confidence scores
        expected_confidence_weighted = (20.0 * 0.9 + (-10.0) * 0.7 + 5.0 * 0.8) / (0.9 + 0.7 + 0.8)
        self.assertAlmostEqual(result['confidence_weighted'], expected_confidence_weighted, places=2)

    def test_classify_sentiment(self):
        """Test sentiment classification logic"""
        test_cases = [
            (15.0, 'bullish'),
            (-15.0, 'bearish'),
            (5.0, 'neutral'),
            (0.0, 'neutral'),
            (10.1, 'bullish'),
            (-10.1, 'bearish')
        ]

        for score, expected_classification in test_cases:
            classification = self.aggregator._classify_sentiment(score)
            self.assertEqual(classification, expected_classification)

    def test_time_weighted_average_same_date(self):
        """Test time weighted average when all articles have same date"""
        base_date = datetime.utcnow()
        scores = [10.0, 20.0, 30.0]
        dates = [base_date, base_date, base_date]

        result = self.aggregator._calculate_time_weighted_average(scores, dates)
        expected = sum(scores) / len(scores)  # Should be simple average
        self.assertEqual(result, expected)

    def test_time_weighted_average_different_dates(self):
        """Test time weighted average with different dates (recent should weigh more)"""
        most_recent = datetime.utcnow()
        older_date = most_recent - timedelta(days=5)

        scores = [10.0, 30.0]  # Older score, newer score
        dates = [older_date, most_recent]

        result = self.aggregator._calculate_time_weighted_average(scores, dates)

        # Newer score should have more weight, so result should be closer to 30 than 20
        simple_average = 20.0
        self.assertGreater(result, simple_average)

    def test_get_empty_sentiment_result(self):
        """Test that empty sentiment result has correct structure"""
        result = self.aggregator._get_empty_sentiment_result()

        required_keys = [
            'sentiment_score', 'simple_average', 'confidence_weighted',
            'time_decay', 'combined_weighted', 'finbert_average',
            'classification', 'confidence_score', 'article_count',
            'score_std', 'date_range', 'raw_scores', 'recent_articles'
        ]

        for key in required_keys:
            self.assertIn(key, result)

        self.assertEqual(result['sentiment_score'], 0.0)
        self.assertEqual(result['classification'], 'neutral')
        self.assertEqual(result['article_count'], 0)
        self.assertEqual(result['raw_scores'], [])
        self.assertEqual(result['recent_articles'], [])

    def test_convenience_functions_exist(self):
        """Test that convenience functions are available"""
        # Test that the convenience functions exist and are callable
        self.assertTrue(callable(mod.update_entity_sentiment_from_recent_news))
        self.assertTrue(callable(mod.update_all_entity_sentiments_from_recent_news))
        self.assertTrue(callable(mod.preview_entity_sentiment_from_recent_news))

    def test_calculate_overall_confidence_same_dates(self):
        """Test overall confidence calculation with same dates"""
        confidences = [0.8, 0.9, 0.7]
        dates = [datetime.utcnow()] * 3

        result = self.aggregator._calculate_overall_confidence(confidences, dates)
        expected = sum(confidences) / len(confidences)
        self.assertAlmostEqual(result, expected, places=5)

    def test_calculate_overall_confidence_bounds(self):
        """Test that overall confidence is bounded between 0.1 and 0.95"""
        confidences = [0.0, 0.0, 0.0]  # Very low confidence
        dates = [datetime.utcnow()] * 3

        result = self.aggregator._calculate_overall_confidence(confidences, dates)
        self.assertGreaterEqual(result, 0.1)
        self.assertLessEqual(result, 0.95)


if __name__ == '__main__':
    unittest.main()