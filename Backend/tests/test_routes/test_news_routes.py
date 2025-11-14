import unittest
from unittest.mock import patch
from app import db
from tests.test_routes.setup_mock_db import test_db
from app.models import News
import uuid

class NewsIngestionTest(unittest.TestCase):
    def _create_sample_news(self):
        """Seed test DB with sample news items."""
        news_items = [
            News(
                id=uuid.uuid4(),
                title="AAPL hits new high",
                description="Apple stock reaches record price",
                url="https://example.com/aapl",
                publisher="MockSource",
                published_date="2025-10-30",
                entities=["AAPL"],
                company_names=["AAPL"],
            ),
            News(
                id=uuid.uuid4(),
                title="TSLA quarterly earnings",
                description="Tesla reports strong Q3 earnings",
                url="https://example.com/tsla",
                publisher="MockSource",
                published_date="2025-10-30",
                entities=["TSLA"],
            ),
            News(
                id=uuid.uuid4(),
                title="Crypto market update",
                description="Bitcoin and Ethereum trends",
                url="https://example.com/crypto",
                publisher="MockSource",
                published_date="2025-10-30",
                entities=["BTC", "ETH"],
            ),
        ]
        db.session.add_all(news_items)
        db.session.commit()
        
        return news_items
    
    @patch("app.routes.news.get_all_ticker_entities", return_value=["AAPL", "TSLA"])
    @patch("app.routes.news.get_gnews_news_by_ticker")
    @patch("time.sleep", return_value=None)  # skip actual sleeping
    def test_automate_news_of_all_entity_by_gnews(self, mock_sleep, mock_get_gnews, mock_get_tickers):
        # Mock the result of GNews for each ticker
        mock_get_gnews.side_effect = [
            {"data": [{"title": "Mock AAPL news", "url": "https://example.com/aapl"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}},
            {"data": [{"title": "Mock TSLA news", "url": "https://example.com/tsla"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}}
        ]

        with test_db() as client:
            response = client.post("/api/news/IngestNewsOfAllEntityByGnews")
            data = response.get_json()

            assert response.status_code == 201
            assert len(data["data"]) == 2  # one article per ticker
            assert "News data generated and saved successfully" in data["message"]
            assert "Total: 2" in data["message"]
            assert "Success: 2" in data["message"]

    @patch("app.routes.news.get_all_ticker_entities", return_value=["AAPL", "TSLA"])
    @patch("app.routes.news.get_gnews_news_by_ticker")
    @patch("app.routes.news.get_finviz_news_by_ticker")
    @patch("app.routes.news.get_all_top_gnews")
    @patch("app.routes.news.get_all_finviz")
    @patch("time.sleep", return_value=None)  # skip actual sleeping
    def test_automate_news_of_entity_and_all(
        self,
        mock_sleep,
        mock_all_finviz,
        mock_all_gnews,
        mock_finviz,
        mock_gnews,
        mock_tickers,
    ):
        # Mock per-ticker news
        mock_gnews.side_effect = [
            {"data": [{"title": "AAPL GNews", "url": "https://example.com/aapl_g"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}},
            {"data": [{"title": "TSLA GNews", "url": "https://example.com/tsla_g"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}}
        ]

        mock_finviz.side_effect = [
            {"data": [{"title": "AAPL Finviz", "url": "https://example.com/aapl_f"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}},
            {"data": [{"title": "TSLA Finviz", "url": "https://example.com/tsla_f"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}}
        ]

        mock_all_gnews.return_value = {
            "data": [{"title": "Top GNews", "url": "https://example.com/top_g"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}
        }

        mock_all_finviz.return_value = {
            "data": [{"title": "All Finviz", "url": "https://example.com/all_f"}],
            "metrics": {"total_articles_fetched": 1, "successful_scrapes": 1, "low_quality_skipped": 0, "failed_scrapes": 0}
        }

        with test_db() as client:
            response = client.post("/api/news/IngestNewsOfEntityAndAll")
            data = response.get_json()
            print(data)

            assert response.status_code == 201
            assert len(data["data"]) == 6  # 2 tickers * 2 (GNews + Finviz) + 2 top/all
            assert "News data generated and saved successfully" in data["message"]
            assert "Total: 6" in data["message"]
            assert "Success: 6" in data["message"]

    # -------------------------------
    # GET /api/news/entity/<entity>
    # -------------------------------
    def test_get_news_by_entity_success(self):
        with test_db() as client:
            self._create_sample_news()
            response = client.get("/api/news/entity/AAPL?page=1&per_page=2")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            print(data)
            self.assertIn("News fetched successfully", data["message"])
            self.assertLessEqual(len(data["data"]["news"]), 2)
            
    # -------------------------------
    # GET /api/news/id/<id>
    # -------------------------------
    def test_get_news_by_id_success(self):
        with test_db() as client:
            news_item = self._create_sample_news()
            response = client.get(f"/api/news/id/{news_item[0].id}")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["data"]["title"], news_item[0].title)

    # -------------------------------
    # GET /api/news/ (all news, paginated)
    # -------------------------------
    def test_get_all_news_success(self):
        with test_db() as client:
            self._create_sample_news()
            response = client.get("/api/news/?page=1&per_page=2")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn("News fetched successfully", data["message"])
            self.assertLessEqual(len(data["data"]["news"]), 2)
