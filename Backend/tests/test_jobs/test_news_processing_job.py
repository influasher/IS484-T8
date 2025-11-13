import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
from datetime import datetime
from app.models import News, Entity, SentimentHistory
from app import db
from tests.test_routes.setup_mock_db import test_db
from jobs.news_processing_job import NewsProcessor


# ------------------------------
# UTILITY TO RUN ASYNC IN SYNC
# ------------------------------
def async_run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

# ------------------------------
# UNIT TESTS
# ------------------------------
class TestNewsProcessorUnit(unittest.TestCase):
    def setUp(self):
        with test_db() as client:
            self.processor = NewsProcessor(client.application)


    @patch("jobs.news_processing_job.SentimentAnalyzer")
    def test_initialize_services(self, mock_analyzer_class):
        mock_instance = MagicMock()
        mock_analyzer_class.return_value = mock_instance

        self.processor.initialize_services()

        self.assertIsNotNone(self.processor.sentiment_analyzer)
        mock_analyzer_class.assert_called_once()

    def test_extract_entities_from_content(self):
        # Patch entity extractors
        content = "Apple is in California, tech sector"
        with patch("jobs.news_processing_job.extract_company", return_value=["Apple"]), \
             patch("jobs.news_processing_job.extract_region", return_value=["California"]), \
             patch("jobs.news_processing_job.extract_sector", return_value=["Tech"]):
            entities = self.processor.extract_entities_from_content(content)
            self.assertEqual(entities["companies"], ["Apple"])
            self.assertEqual(entities["regions"], ["California"])
            self.assertEqual(entities["sectors"], ["Tech"])

    @patch("app.services.sentiment_analysis.get_sentiment")
    def test_analyze_sentiment_returns_scores(self, mock_get_sentiment):
        mock_get_sentiment.return_value = {
            "classification": "bullish",
            "numerical_score": 0.8,
            "confidence": 0.9,
            "agreement_rate": 0.7,
            "finbert_score": 0.75,
            "second_model_score": 0.8,
            "third_model_score": 0.85,
            "shap": None,
            "shap_html": None
        }

        result = self.processor.analyze_sentiment("some content", title="Title")
        self.assertEqual(result["sentiment"], "bullish")
        self.assertAlmostEqual(result["score"], 0.8)
        self.assertAlmostEqual(result["confidence"], 0.9)

    @patch("jobs.news_processing_job.scrape_article_async", new_callable=AsyncMock)
    def test_scrape_article_content_fallback(self, mock_scrape):
        mock_scrape.return_value = """
            <html><body>
            <p>This is some article text that is definitely longer than fifty characters so that newspaper can parse it.</p>
            <p>Another paragraph to satisfy the parser.</p>
            </body></html>
        """
        result = async_run(self.processor.scrape_article_content("http://example.com"))
        self.assertIsNotNone(result)
        self.assertIn("content", result)

# ------------------------------
# INTEGRATION TESTS WITH DB
# ------------------------------
class TestNewsProcessorIntegration(unittest.TestCase):
    def setUp(self):
        with test_db() as client:
            self.processor = NewsProcessor(client.application)

    def _seed_data(self):
        entity = Entity(name="Apple", ticker="AAPL")
        db.session.add(entity)
        db.session.commit()
        self.entity_id = entity.id

    @patch("gnews.GNews")
    def test_fetch_news_urls_integration(self, mock_gnews_class):
        with test_db() as client:
            self._seed_data()
            # Mock GNews API to return articles
            mock_gn_instance = MagicMock()
            mock_gn_instance.get_news.return_value = [
                {
                    "url": "http://example.com/article1",
                    "title": "Apple launches new product",
                    "publisher": {"title": "TechNews"},
                    "published date": "Wed, 13 Nov 2025 12:00:00 GMT",
                    "description": "Apple product description"
                }
            ]
            mock_gnews_class.return_value = mock_gn_instance

            # Run
            result = async_run(self.processor.fetch_news_urls(lookback_days=1))

            # Assertions
            self.assertTrue(len(result) > 0)
            article = result[0]
            self.assertEqual(article["entity_name"], "Apple")
            self.assertEqual(article["entity_id"], self.entity_id)
            self.assertEqual(article["title"], "Apple launches new product")
            self.assertIsInstance(article["published_date"], datetime)

    @patch("jobs.news_processing_job.NewsProcessor.analyze_sentiment")
    @patch("jobs.news_processing_job.NewsProcessor.extract_entities_from_content")
    @patch("jobs.news_processing_job.scrape_article_async", new_callable=AsyncMock)
    def test_save_to_database_creates_news(self, mock_scrape, mock_extract, mock_sentiment):
        with test_db() as client:
            self._seed_data()

            # Mock scraping
            mock_scrape.return_value = "<html><body>Apple released new iPhone.</body></html>"

            # Mock entity extraction
            mock_extract.return_value = {
                "companies": ["Apple"],
                "regions": ["US"],
                "sectors": ["Technology"]
            }

            # Mock sentiment
            mock_sentiment.return_value = {
                "finbert_score": 0.5,
                "second_model_score": 0.6,
                "third_model_score": 0.55,
                "score": 0.55,
                "sentiment": "bullish",
                "confidence": 0.9,
                "agreement_rate": 0.8,
                "shap": None,
                "shap_html": None
            }

            # URL data
            url_data = {
                "url": "http://example.com/article1",
                "title": "Apple Event",
                "publisher": "TechNews",
                "description": "Apple released a new product",
                "entity_name": "Apple",
                "entity_id": self.entity_id
            }

            # Run the async process
            news = async_run(self.processor.process_article(url_data))

            # Assertions
            fetched = News.query.filter_by(url=url_data["url"]).first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.title, "Apple Event")
            self.assertEqual(fetched.sentiment, "bullish")
            self.assertAlmostEqual(fetched.score, 0.55)
            self.assertEqual(fetched.company_names, ["Apple"])
            self.assertIn("US", fetched.regions)
            self.assertIn("Technology", fetched.sectors)

    # def test_update_sentiment_history_creates_entries(self):
    #     # Add News entries
    #     with test_db() as client:
    #         self._seed_data()
    #         news = News(
    #             url="http://example.com/1",
    #             title="Apple News",
    #             content="Apple does something",
    #             company_names=["Apple"],
    #             score=0.6,
    #             confidence=0.9,
    #             sentiment="bullish",
    #             scraped_at=datetime.utcnow(),
    #             published_date=datetime.utcnow()  # <-- required
    #         )
    #         db.session.add(news)
    #         db.session.commit()
            
    #         self.processor.update_sentiment_history([news])

    #         all = SentimentHistory.query.all()
    #         print(all)

    #         history = SentimentHistory.query.filter_by(entity_id=self.entity_id).first()
    #         self.assertIsNotNone(history)
    #         self.assertEqual(history.article_count, 1)
    #         self.assertEqual(history.sentiment, "positive")

    @patch.object(NewsProcessor, "initialize_services")
    @patch.object(NewsProcessor, "fetch_news_urls", new_callable=AsyncMock)
    @patch.object(NewsProcessor, "process_article", new_callable=AsyncMock)
    @patch.object(NewsProcessor, "update_sentiment_history")
    def test_run_processes_articles(
        self, mock_update_history, mock_process_article, mock_fetch_urls, mock_init_services
    ):
        with test_db() as client:
            # Arrange
            fake_urls = [
                {"url": "http://example.com/article1", "title": "Title1"},
                {"url": "http://example.com/article2", "title": "Title2"}
            ]
            mock_fetch_urls.return_value = fake_urls

            fake_news_objects = [
                MagicMock(spec=News, title="Title1"),
                MagicMock(spec=News, title="Title2")
            ]
            mock_process_article.side_effect = fake_news_objects  # returns a different article each time

            # Act
            async_run(self.processor.run(lookback_days=2, max_articles=None))

            # Assert
            mock_init_services.assert_called_once()
            mock_fetch_urls.assert_awaited_once_with(2)
            self.assertEqual(mock_process_article.await_count, len(fake_urls))
            mock_update_history.assert_called_once_with(fake_news_objects)

    @patch.object(NewsProcessor, "fetch_news_urls", new_callable=AsyncMock)
    @patch.object(NewsProcessor, "initialize_services")
    def test_run_no_articles(self, mock_init_services, mock_fetch_urls):
        # Arrange
        mock_fetch_urls.return_value = []

        # Act
        async_run(self.processor.run(lookback_days=1))

        # Assert
        mock_init_services.assert_called_once()
        mock_fetch_urls.assert_awaited_once_with(1)
        # update_sentiment_history should not be called if no articles

    def test_save_to_database_existing_article(self):
        with test_db() as client:
            self._seed_data()
            # Create article first
            news = News(
                url="http://example.com/existing",
                title="Existing Article",
                company_names=["Apple"],
                published_date=datetime.utcnow(),
                scraped_at=datetime.utcnow()
            )
            db.session.add(news)
            db.session.commit()

            result = self.processor.save_to_database(
                url="http://example.com/existing",
                title="Should Not Override",
                content="New content",
                published_date=datetime.utcnow(),
                entities={"companies": ["Apple"], "regions": [], "sectors": []},
                sentiment={"score": 0.5, "sentiment": "bullish"}
            )

            # Should return the existing object
            self.assertEqual(result.id, news.id)
            self.assertEqual(result.title, "Existing Article")

    def test_update_sentiment_history_empty_list(self):
        with test_db() as client:
            self._seed_data()
            # Call with empty list
            self.processor.update_sentiment_history([])
            # Should not raise, and no entries created
            histories = SentimentHistory.query.all()
            self.assertEqual(len(histories), 0)

    @patch("jobs.news_processing_job.scrape_article_async", new_callable=AsyncMock)
    def test_process_article_scrape_failure(self, mock_scrape):
        with test_db() as client:
            self._seed_data()
            mock_scrape.return_value = None  # Simulate scrape fail
            url_data = {
                "url": "http://example.com/fail",
                "title": "Fail Article",
                "description": "Fallback description",
                "entity_name": "Apple",
                "entity_id": self.entity_id
            }
            news = async_run(self.processor.process_article(url_data))
            self.assertIsNotNone(news)
            self.assertEqual(news.content, "Fallback description")

    def test_extract_entities_from_content_error(self):
        with patch("jobs.news_processing_job.extract_company", side_effect=Exception("Fail")), \
            patch("jobs.news_processing_job.extract_region", side_effect=Exception("Fail")), \
            patch("jobs.news_processing_job.extract_sector", side_effect=Exception("Fail")):
            result = self.processor.extract_entities_from_content("Some content")
            self.assertEqual(result, {"companies": [], "regions": [], "sectors": []})

    @patch("app.services.sentiment_analysis.get_sentiment", side_effect=Exception("Fail"))
    def test_analyze_sentiment_exception(self, mock_sentiment):
        result = self.processor.analyze_sentiment("Some content")
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["score"], 0.0)

    @patch("jobs.news_processing_job.scrape_article_async", new_callable=AsyncMock)
    def test_scrape_article_content_too_short(self, mock_scrape):
        mock_scrape.return_value = "<html><body>Short</body></html>"
        result = async_run(self.processor.scrape_article_content("http://example.com"))
        self.assertIsNone(result)

    @patch.object(NewsProcessor, "initialize_services")
    @patch.object(NewsProcessor, "fetch_news_urls", new_callable=AsyncMock)
    @patch.object(NewsProcessor, "process_article", new_callable=AsyncMock)
    @patch.object(NewsProcessor, "update_sentiment_history")
    def test_run_with_failed_articles(self, mock_update, mock_process, mock_fetch, mock_init):
        with test_db() as client:
            fake_urls = [{"url": "http://example.com/1"}, {"url": "http://example.com/2"}]
            mock_fetch.return_value = fake_urls
            # Simulate first fails, second succeeds
            mock_process.side_effect = [None, MagicMock(spec=News)]
            async_run(self.processor.run())
            self.assertEqual(mock_process.await_count, 2)
            mock_update.assert_called_once()








if __name__ == "__main__":
    unittest.main()
