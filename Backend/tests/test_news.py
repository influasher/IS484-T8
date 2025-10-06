import unittest
import os
import sys
import uuid
import random
import string
from datetime import datetime
from unittest.mock import patch

from app import create_app, db
from app.models.news import News

# Make sure we can import the blueprint module under both layouts
try:
    from app.routes import news as news_module
except Exception:
    import news as news_module  # fallback if your module path is flat


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class BaseTestCase(unittest.TestCase):
    """Base test case with app context and database setup."""

    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["TESTING"] = True

        # If the news blueprint isn't registered by your factory, register it here.
        if "news" not in self.app.blueprints:
            self.app.register_blueprint(news_module.news_bp, url_prefix="/news")

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up after tests with proper cascade handling."""
        try:
            # Clear all sessions and rollback transactions
            db.session.rollback()
            db.session.remove()

            # Handle PostgreSQL foreign key constraints
            if db.engine.dialect.name == 'postgresql':
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text('DROP TABLE IF EXISTS client_portfolio CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS transactions CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS news CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS entity CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE'))
                    conn.commit()
            else:
                # For SQLite
                db.drop_all()

        except Exception as e:
            print(f"Warning: Error during news test teardown: {e}")
        finally:
            super().tearDown()


# --------------------------------------------------------------------------------------
# Existing News model CRUD & constraints tests (kept, slightly adapted to use BaseTestCase.client)
# --------------------------------------------------------------------------------------

class NewsModelTestCase(BaseTestCase):
    """Test cases for News model functionality."""

    def setUp(self):
        super().setUp()
        self.test_counter = 0

    def generate_unique_url(self):
        """Generate a unique URL for testing."""
        self.test_counter += 1
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"https://test-news-{self.test_counter}-{random_suffix}.example.com"

    def create_test_news(self, **kwargs):
        """Create a test news item with unique constraints."""
        default_data = {
            'id': uuid.uuid4(),
            'publisher': f'test_publisher_{self.test_counter}',
            'description': f'Test news description {self.test_counter}',
            'published_date': datetime.now().strftime('%Y-%m-%d'),
            'title': f'Test News {self.test_counter} {uuid.uuid4().hex[:8]}',
            'url': self.generate_unique_url(),
            'entities': [f'TestEntity_{self.test_counter}'],
            'score': 0.7,
            'sentiment': 'Positive',
            'summary': f'Test news summary {self.test_counter}'
        }
        default_data.update(kwargs)

        news = News(**default_data)
        db.session.add(news)
        db.session.commit()
        return news

    def test_create_news(self):
        news = self.create_test_news()
        self.assertIsNotNone(news)
        self.assertIsNotNone(news.title)
        self.assertIsNotNone(news.url)

    def test_read_news(self):
        unique_title = f'Test Read News {uuid.uuid4().hex[:8]}'
        self.create_test_news(title=unique_title)

        found_news = News.query.filter_by(title=unique_title).first()
        self.assertIsNotNone(found_news)
        self.assertEqual(found_news.title, unique_title)

    def test_update_news(self):
        original_title = f'Original Title {uuid.uuid4().hex[:8]}'
        news = self.create_test_news(title=original_title)

        updated_title = f'Updated Title {uuid.uuid4().hex[:8]}'
        news.title = updated_title
        news.sentiment = 'Negative'
        db.session.commit()

        updated_news = News.query.get(news.id)
        self.assertEqual(updated_news.title, updated_title)
        self.assertEqual(updated_news.sentiment, 'Negative')

    def test_delete_news(self):
        news = self.create_test_news()
        news_id = news.id

        db.session.delete(news)
        db.session.commit()

        deleted_news = News.query.get(news_id)
        self.assertIsNone(deleted_news)

    def test_news_unique_url_constraint(self):
        unique_url = self.generate_unique_url()
        _ = self.create_test_news(title='First News', url=unique_url)

        news2 = News(
            id=uuid.uuid4(),
            title='Second News',
            url=unique_url,  # Duplicate URL should violate unique constraint
            publisher='test_publisher_2',
            description='Another test description',
            published_date=datetime.now().strftime('%Y-%m-%d'),
            sentiment='Neutral'
        )

        db.session.add(news2)
        with self.assertRaises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_news_serialization(self):
        news = self.create_test_news(title='Serialization Test', url=self.generate_unique_url())
        if hasattr(news, 'to_dict'):
            news_dict = news.to_dict()
            self.assertIsInstance(news_dict, dict)
            self.assertEqual(news_dict['title'], 'Serialization Test')
            self.assertIn('id', news_dict)
            self.assertIn('url', news_dict)


# --------------------------------------------------------------------------------------
# Route tests for app.routes.news blueprint (service calls are monkeypatched)
# --------------------------------------------------------------------------------------

class NewsRoutesTestCase(BaseTestCase):

    # ---- /news/gnews/premium ----
    def test_gnews_premium_success_201(self):
        payload = {"entity": "AAPL"}
        with patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_premium_news_sources", return_value=[{"title": "AAPL 1"}]):
            resp = self.client.post("/news/gnews/premium", json=payload)
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertIn("News data generated", body["message"])
        self.assertIsInstance(body["data"], list)
        self.assertGreater(len(body["data"]), 0)

    def test_gnews_premium_not_found_404(self):
        payload = {"entity": "AAPL"}
        with patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_premium_news_sources", return_value=[]):
            resp = self.client.post("/news/gnews/premium", json=payload)
        self.assertEqual(resp.status_code, 404)

    # ---- /news/gnews ----
    def test_gnews_ingest_success_201(self):
        with patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_gnews_news_by_ticker", return_value=[{"title": "T1"}]):
            resp = self.client.post("/news/gnews", json={"entity": "MSFT"})
        self.assertEqual(resp.status_code, 201)
        self.assertGreater(len(resp.get_json()["data"]), 0)

    def test_gnews_ingest_not_found_404(self):
        with patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_gnews_news_by_ticker", return_value=[]):
            resp = self.client.post("/news/gnews", json={"entity": "MSFT"})
        self.assertEqual(resp.status_code, 404)

    # ---- /news/finviz ----
    def test_finviz_ingest_success_201(self):
        with patch.object(news_module, "get_finviz_news_by_ticker", return_value=[{"title": "F1"}]):
            resp = self.client.post("/news/finviz", json={"entity": "GOOG"})
        self.assertEqual(resp.status_code, 201)
        self.assertGreater(len(resp.get_json()["data"]), 0)

    def test_finviz_ingest_not_found_404(self):
        with patch.object(news_module, "get_finviz_news_by_ticker", return_value=[]):
            resp = self.client.post("/news/finviz", json={"entity": "GOOG"})
        self.assertEqual(resp.status_code, 404)

    # ---- /news/yfinance ----
    def test_yfinance_ingest_success_201(self):
        with patch.object(news_module, "get_stock_news", return_value=[{"title": "YF1"}]):
            resp = self.client.post("/news/yfinance", json={"entity": "NVDA"})
        self.assertEqual(resp.status_code, 201)
        self.assertGreater(len(resp.get_json()["data"]), 0)

    def test_yfinance_ingest_not_found_404(self):
        with patch.object(news_module, "get_stock_news", return_value=[]):
            resp = self.client.post("/news/yfinance", json={"entity": "NVDA"})
        self.assertEqual(resp.status_code, 404)

    # ---- /news/all ----
    def test_all_ingest_aggregates_metrics_201(self):
        gnews = {
            "data": [{"title": "G1"}],
            "metrics": {
                "total_articles_fetched": 5,
                "successful_scrapes": 4,
                "low_quality_skipped": 1,
                "failed_scrapes": 0,
            },
        }
        finviz = {
            "data": [{"title": "F1"}],
            "metrics": {
                "total_articles_fetched": 3,
                "successful_scrapes": 3,
                "low_quality_skipped": 0,
                "failed_scrapes": 0,
            },
        }
        with patch.object(news_module, "get_all_top_gnews", return_value=gnews), \
             patch.object(news_module, "get_all_finviz", return_value=finviz):
            resp = self.client.post("/news/all")
        self.assertEqual(resp.status_code, 201)
        msg = resp.get_json()["message"]
        self.assertIn("Success Rate", msg)
        self.assertEqual(len(resp.get_json()["data"]), 2)

    def test_all_ingest_empty_404(self):
        with patch.object(news_module, "get_all_top_gnews", return_value={"data": [], "metrics": {}}), \
             patch.object(news_module, "get_all_finviz", return_value={"data": [], "metrics": {}}):
            resp = self.client.post("/news/all")
        self.assertEqual(resp.status_code, 404)

    # ---- /news/IngestNewsOfAllEntityByGnews ----
    def test_ingest_all_entity_by_gnews_success_201(self):
        with patch.object(news_module, "get_all_ticker_entities", return_value=["AAPL", "MSFT"]), \
             patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_gnews_news_by_ticker", side_effect=[
                 {"data": [{"title": "AAPL-1"}], "metrics": {
                     "total_articles_fetched": 2, "successful_scrapes": 2, "low_quality_skipped": 0, "failed_scrapes": 0
                 }},
                 {"data": [{"title": "MSFT-1"}], "metrics": {
                     "total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0
                 }},
             ]), \
             patch.object(news_module.time, "sleep", side_effect=lambda *_: None):
            resp = self.client.post("/news/IngestNewsOfAllEntityByGnews")
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertGreaterEqual(len(body["data"]), 2)
        self.assertIn("Success Rate", body["message"])

    def test_ingest_all_entity_by_gnews_empty_404(self):
        with patch.object(news_module, "get_all_ticker_entities", return_value=["AAPL"]), \
             patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_gnews_news_by_ticker", return_value={
                 "data": [], "metrics": {
                     "total_articles_fetched": 0, "successful_scrapes": 0,
                     "low_quality_skipped": 0, "failed_scrapes": 0
                 }
             }), \
             patch.object(news_module.time, "sleep", side_effect=lambda *_: None):
            resp = self.client.post("/news/IngestNewsOfAllEntityByGnews")
        self.assertEqual(resp.status_code, 404)

    # ---- /news/IngestNewsOfEntityAndAll ----
    def test_ingest_entity_and_all_success_201(self):
        with patch.object(news_module, "get_all_ticker_entities", return_value=["TSLA"]), \
             patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_gnews_news_by_ticker", return_value={
                 "data": [{"title": "TSLA-G"}],
                 "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1,
                             "low_quality_skipped": 0, "failed_scrapes": 0}
             }), \
             patch.object(news_module, "get_finviz_news_by_ticker", return_value={
                 "data": [{"title": "TSLA-F"}],
                 "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1,
                             "low_quality_skipped": 0, "failed_scrapes": 0}
             }), \
             patch.object(news_module, "get_all_top_gnews", return_value={
                 "data": [{"title": "TOP-G"}],
                 "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1,
                             "low_quality_skipped": 0, "failed_scrapes": 0}
             }), \
             patch.object(news_module, "get_all_finviz", return_value={
                 "data": [{"title": "ALL-F"}],
                 "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1,
                             "low_quality_skipped": 0, "failed_scrapes": 0}
             }), \
             patch.object(news_module.time, "sleep", side_effect=lambda *_: None):
            resp = self.client.post("/news/IngestNewsOfEntityAndAll")
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()["data"]
        # Expect at least 4 items from: per-ticker gnews + per-ticker finviz + top gnews + all finviz
        self.assertGreaterEqual(len(data), 4)

    def test_ingest_entity_and_all_empty_404(self):
        with patch.object(news_module, "get_all_ticker_entities", return_value=["TSLA"]), \
             patch.object(news_module, "format_date_into_tuple_for_gnews", side_effect=lambda d: d), \
             patch.object(news_module, "get_gnews_news_by_ticker", return_value={"data": [], "metrics": {}}), \
             patch.object(news_module, "get_finviz_news_by_ticker", return_value={"data": [], "metrics": {}}), \
             patch.object(news_module, "get_all_top_gnews", return_value={"data": [], "metrics": {}}), \
             patch.object(news_module, "get_all_finviz", return_value={"data": [], "metrics": {}}), \
             patch.object(news_module.time, "sleep", side_effect=lambda *_: None):
            resp = self.client.post("/news/IngestNewsOfEntityAndAll")
        self.assertEqual(resp.status_code, 404)

    # ---- /news/resync ----
    def test_resync_success_201(self):
        with patch.object(news_module, "resync_news_data", return_value=[{"id": "ok"}]):
            resp = self.client.post("/news/resync")
        self.assertEqual(resp.status_code, 201)
        self.assertGreater(len(resp.get_json()["data"]), 0)

    def test_resync_not_found_404(self):
        with patch.object(news_module, "resync_news_data", return_value=[]):
            resp = self.client.post("/news/resync")
        self.assertEqual(resp.status_code, 404)

    # ---- /news/entity/<entity> ----
    def test_get_news_by_entity_success_200_with_query_args(self):
        fake_list = [{"title": "AAPL item 1"}, {"title": "AAPL item 2"}]
        with patch.object(news_module, "news_by_name", return_value=fake_list):
            resp = self.client.get("/news/entity/AAPL?page=2&per_page=3&sort_order=asc&filter=week")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["data"], fake_list)

    def test_get_news_by_entity_not_found_404(self):
        with patch.object(news_module, "news_by_name", return_value=[]):
            resp = self.client.get("/news/entity/UNKNOWN")
        self.assertEqual(resp.status_code, 404)

    # ---- /news/id/<uuid> ----
    def test_get_news_by_id_success_200(self):
        nid = uuid.uuid4()
        with patch.object(news_module, "news_by_id", return_value={"id": str(nid), "title": "X"}):
            resp = self.client.get(f"/news/id/{nid}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["data"]["id"], str(nid))

    def test_get_news_by_id_not_found_404(self):
        nid = uuid.uuid4()
        with patch.object(news_module, "news_by_id", return_value=None):
            resp = self.client.get(f"/news/id/{nid}")
        self.assertEqual(resp.status_code, 404)

    # ---- /news/?page=...&per_page=...&search=... ----
    def test_get_all_news_success_200_with_query_params(self):
        fake_list = [{"title": "hello"}, {"title": "world"}]
        with patch.object(news_module, "all_news", return_value=fake_list):
            resp = self.client.get("/news/?page=1&per_page=4&search=apple&sort_order=desc&filter=month")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["data"], fake_list)

    def test_get_all_news_not_found_404(self):
        with patch.object(news_module, "all_news", return_value=[]):
            resp = self.client.get("/news/")
        self.assertEqual(resp.status_code, 404)