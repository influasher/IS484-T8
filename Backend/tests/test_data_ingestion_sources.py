import unittest
import types
import time as _time
import json
import datetime
from unittest.mock import patch, MagicMock
import pandas as pd

# Try app-layout imports first, fall back to flat layout if needed
try:
    from app.services import data_ingestion_finviz as finviz_mod
    from app.services import data_ingestion_gnews as gnews_mod
    from app.services import data_ingestion_yfinance as yfin_mod
except Exception:
    import data_ingestion_finviz as finviz_mod  # type: ignore
    import data_ingestion_gnews as gnews_mod    # type: ignore
    import data_ingestion_yfinance as yfin_mod  # type: ignore


# -----------------------------
# Common lightweight DB & Model stubs
# -----------------------------

class _DBStub:
    class session:
        @staticmethod
        def add(obj): pass
        @staticmethod
        def commit(): pass

class _NewsModelStub:
    """Emulates NewsModel.query.filter_by(url=...).first() for duplicate checks."""
    existing_urls = set()
    class query:
        @staticmethod
        def filter_by(url=None, **kw):
            class _Q:
                @staticmethod
                def first():
                    return object() if url in _NewsModelStub.existing_urls else None
            return _Q()
    def __init__(self, **kwargs):
        # Accept any constructor args used by service code
        # Keep URL accessible for potential future checks
        self.url = kwargs.get("url")
        self.__dict__.update(kwargs)


# -----------------------------
# Tests for Finviz ingestion
# -----------------------------

class FinvizIngestionTests(unittest.TestCase):
    def setUp(self):
        # Ensure module uses our DB and NewsModel stubs
        self.db_patch = patch.object(finviz_mod, "db", _DBStub)
        self.news_patch = patch.object(finviz_mod, "NewsModel", _NewsModelStub)
        self.db_patch.start()
        self.news_patch.start()

        # Avoid real sleeps; track calls
        self.sleep_patch = patch.object(finviz_mod.time, "sleep")
        self.mock_sleep = self.sleep_patch.start()

        # Default helper behavior
        self.scrape_patch = patch.object(finviz_mod, "scrape_article", return_value="<html>ok</html>")
        self.details_patch = patch.object(finviz_mod, "get_article_details", return_value={
            "text": "body text",
            "summary": "sum",
            "numerical_score": 0.3,
            "finbert_score": 0.25,
            "second_model_score": 0.35,
            "third_model_score": 0.20,
            "classification": "Positive",
            "keywords": ["k1", "k2"],
            "confidence": 0.8,
            "agreement_rate": 0.9,
            "companies": ["AAPL"],
            "regions": ["US"],
            "sectors": ["Tech"],
        })
        self.quality_patch = patch.object(finviz_mod, "evaluate_scraping_quality", return_value={"is_clean": True})
        self.mock_scrape = self.scrape_patch.start()
        self.mock_details = self.details_patch.start()
        self.mock_quality = self.quality_patch.start()

    def tearDown(self):
        self.mock_quality.stop()
        self.details_patch.stop()
        self.scrape_patch.stop()
        self.sleep_patch.stop()
        self.news_patch.stop()
        self.db_patch.stop()
        _NewsModelStub.existing_urls.clear()

    def _today(self):
        return datetime.datetime.today().strftime("%Y-%m-%d")

    def _yesterday(self):
        return (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    def test_get_finviz_news_by_ticker_happy_path_one_item(self):
        today = self._today()
        # Finviz stock stub
        class _Stock:
            def ticker_news(self):
                # Finviz returns list of rows; we adapt to DataFrame columns ["Date","Title","Link","Source"]
                return [
                    [f"{today} 12:00PM", "T1", "https://ex/1", "SrcA"],
                    [f"2020-01-01 12:00PM", "Old", "https://ex/old", "SrcB"],  # filtered by date
                ]
        with patch.object(finviz_mod, "finvizfinance", return_value=_Stock()):
            out = finviz_mod.get_finviz_news_by_ticker("AAPL")

        self.assertIn("data", out)
        self.assertEqual(len(out["data"]), 1)
        self.assertEqual(out["data"][0]["title"], "T1")
        metrics = out["metrics"]
        self.assertEqual(metrics["total_articles_fetched"], 1)
        self.assertEqual(metrics["successful_scrapes"], 1)
        self.assertEqual(metrics["failed_scrapes"], 0)
        self.assertEqual(metrics["low_quality_skipped"], 0)
        self.assertEqual(metrics["scrape_success_rate"], 1.0)

    def test_get_finviz_news_by_ticker_duplicate_skipped(self):
        today = self._today()
        _NewsModelStub.existing_urls.add("https://ex/dup")
        class _Stock:
            def ticker_news(self):
                return [[f"{today} 08:00AM", "Dup", "https://ex/dup", "Src"]]
        with patch.object(finviz_mod, "finvizfinance", return_value=_Stock()):
            out = finviz_mod.get_finviz_news_by_ticker("TSLA")
        # duplicate -> no data added, but total_articles_fetched increments
        self.assertEqual(out["metrics"]["total_articles_fetched"], 1)
        self.assertEqual(len(out["data"]), 0)
        # No scrape/commit attempted on duplicate

    def test_get_finviz_news_by_ticker_low_quality_skipped(self):
        today = self._today()
        class _Stock:
            def ticker_news(self):
                return [[f"{today} 10:10AM", "LowQ", "https://ex/lowq", "Src"]]
        with patch.object(finviz_mod, "finvizfinance", return_value=_Stock()), \
             patch.object(finviz_mod, "evaluate_scraping_quality", return_value={"is_clean": False}):
            out = finviz_mod.get_finviz_news_by_ticker("MSFT")
        self.assertEqual(out["metrics"]["total_articles_fetched"], 1)
        self.assertEqual(out["metrics"]["low_quality_skipped"], 1)
        self.assertEqual(out["metrics"]["successful_scrapes"], 0)
        self.assertEqual(len(out["data"]), 0)

    def test_get_finviz_news_by_ticker_scrape_failure(self):
        today = self._today()
        class _Stock:
            def ticker_news(self):
                return [[f"{today} 10:10AM", "Bad", "https://ex/fail", "Src"]]
        with patch.object(finviz_mod, "finvizfinance", return_value=_Stock()), \
             patch.object(finviz_mod, "scrape_article", return_value=None):
            out = finviz_mod.get_finviz_news_by_ticker("MSFT")
        self.assertEqual(out["metrics"]["failed_scrapes"], 1)
        self.assertEqual(out["metrics"]["successful_scrapes"], 0)
        self.assertEqual(len(out["data"]), 0)

    def test_get_finviz_news_by_ticker_rate_limit_sleeps(self):
        today = self._today()
        rows = [[f"{today} 09:{i:02d}AM", f"T{i}", f"https://ex/{i}", "Src"]
                for i in range(16)]  # triggers >15 threshold once
        class _Stock:
            def ticker_news(self):
                return rows
        with patch.object(finviz_mod, "finvizfinance", return_value=_Stock()):
            finviz_mod.get_finviz_news_by_ticker("NVDA")
        self.mock_sleep.assert_called()  # rate-limit sleep invoked at least once

    def test_get_finviz_news_by_ticker_constructor_error(self):
        with patch.object(finviz_mod, "finvizfinance", side_effect=RuntimeError("boom")):
            out = finviz_mod.get_finviz_news_by_ticker("BAD")
        self.assertEqual(out["metrics"]["total_articles_fetched"], 0)
        self.assertEqual(out["data"], [])

    def test_get_all_finviz_happy_path(self):
        today = self._today()
        older = "2020-01-01"
        class _NewsAPI:
            def get_news(self):
                return {
                    "news": [
                        [f"{today} 12:00PM", "TodayTitle", "https://ex/today", "SrcX"],
                        [f"{older} 12:00PM", "OldTitle", "https://ex/old", "SrcY"],  # filtered by date
                    ]
                }
        with patch.object(finviz_mod, "News", return_value=_NewsAPI()):
            out = finviz_mod.get_all_finviz()
        self.assertEqual(len(out["data"]), 1)
        self.assertEqual(out["data"][0]["title"], "TodayTitle")
        m = out["metrics"]
        self.assertEqual(m["total_articles_fetched"], 1)
        self.assertEqual(m["successful_scrapes"], 1)
        self.assertEqual(m["failed_scrapes"], 0)
        self.assertEqual(m["low_quality_skipped"], 0)

    def test_get_stock_fundamentals_passthrough(self):
        class _Stock:
            def ticker_fundament(self): return {"P/E": 30, "EPS": 5.1}
        with patch.object(finviz_mod, "finvizfinance", return_value=_Stock()):
            out = finviz_mod.get_stock_fundamentals("AAPL")
        self.assertEqual(out, {"P/E": 30, "EPS": 5.1})


# -----------------------------
# Tests for GNews ingestion
# -----------------------------

class GNewsIngestionTests(unittest.TestCase):
    def setUp(self):
        # Replace DB and News model within gnews module helpers
        self.db_patch = patch.object(gnews_mod, "db", _DBStub)
        self.db_patch.start()
        # Avoid real sleeps
        self.sleep_patch = patch.object(gnews_mod.time, "sleep")
        self.mock_sleep = self.sleep_patch.start()

        # Defaults
        self.scrape_patch = patch.object(gnews_mod, "scrape_article", return_value="<html>ok</html>")
        self.details_patch = patch.object(gnews_mod, "get_article_details", return_value={
            "text": "body text",
            "summary": "sum",
            "numerical_score": 0.4,
            "finbert_score": 0.3,
            "second_model_score": 0.5,
            "third_model_score": 0.2,
            "classification": "Positive",
            "keywords": ["k1"],
            "confidence": 0.85,
            "agreement_rate": 0.9,
            "companies": ["TSLA"],
            "regions": ["US"],
            "sectors": ["Auto"],
            "shap": "SHAP_JSON"
        })
        self.quality_patch = patch.object(gnews_mod, "evaluate_scraping_quality", return_value={"is_clean": True})
        self.url_patch = patch.object(gnews_mod, "URL_decoder", side_effect=lambda u: {"decoded_url": u})
        self.insert_patch = patch.object(gnews_mod, "insert_data_to_db", return_value=True)
        self.exists_patch = patch.object(gnews_mod, "check_if_data_exists", return_value=False)

        self.scrape_patch.start()
        self.details_patch.start()
        self.quality_patch.start()
        self.url_patch.start()
        self.insert_patch.start()
        self.exists_patch.start()

    def tearDown(self):
        self.exists_patch.stop()
        self.insert_patch.stop()
        self.url_patch.stop()
        self.quality_patch.stop()
        self.details_patch.stop()
        self.scrape_patch.stop()
        self.sleep_patch.stop()
        self.db_patch.stop()

    def test_get_premium_news_sources_happy_path(self):
        # Limit premium sources to one entry for test
        premium = {"reuters.com": {"reliability": 0.9, "paywall": False, "specialization": ["markets"], "max_results": 2}}
        class _GNews:
            def __init__(self, *a, **k): pass
            def get_news(self, q): return [{"url": "https://reuters.com/a1"}]

        with patch.object(gnews_mod, "PREMIUM_SOURCES", premium), \
             patch.object(gnews_mod, "GNews", _GNews):
            out = gnews_mod.get_premium_news_sources("AAPL", (2025, 10, 5), (2025, 10, 6))

        self.assertEqual(len(out["data"]), 1)
        m = out["metrics"]
        self.assertEqual(m["total_articles_fetched"], 1)
        self.assertEqual(m["successful_scrapes"], 1)
        self.assertEqual(m["failed_scrapes"], 0)
        self.assertEqual(m.get("paywall_flagged", 0), 0)

    def test_get_premium_news_sources_paywalled_skipped(self):
        premium = {"ft.com": {"reliability": 0.9, "paywall": True, "specialization": ["global"], "max_results": 1}}
        class _GNews:
            def __init__(self, *a, **k): pass
            def get_news(self, q): return [{"url": "https://ft.com/a-pay"}]
        # Make HTML obviously paywalled to trigger looks_paywalled
        with patch.object(gnews_mod, "PREMIUM_SOURCES", premium), \
             patch.object(gnews_mod, "GNews", _GNews), \
             patch.object(gnews_mod, "scrape_article", return_value="Subscribe to continue..."):
            out = gnews_mod.get_premium_news_sources("MSFT", (2025, 10, 5), (2025, 10, 6))
        m = out["metrics"]
        self.assertEqual(m["total_articles_fetched"], 1)
        self.assertEqual(m["successful_scrapes"], 0)
        self.assertEqual(m["paywall_flagged"], 1)

    def test_get_gnews_news_by_ticker_success_and_metrics(self):
        class _GNews:
            def __init__(self, *a, **k): pass
            def get_news(self, q): return [
                {"url": "https://ex.com/a"}, {"url": "https://ex.com/b"}
            ]

        with patch.object(gnews_mod, "GNews", _GNews):
            out = gnews_mod.get_gnews_news_by_ticker("TSLA", (2025,1,1), (2025,1,2))

        self.assertEqual(len(out["data"]), 2)
        m = out["metrics"]
        self.assertEqual(m["total_articles_fetched"], 2)
        self.assertEqual(m["successful_scrapes"], 2)
        self.assertEqual(m["failed_scrapes"], 0)
        self.assertEqual(m["low_quality_skipped"], 0)

    def test_get_all_top_gnews_filters_by_date_and_inserts(self):
        # Build a "today" RFC-like timestamp that matches parser in code
        now = datetime.datetime.utcnow()
        today_str = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
        older_str = "Mon, 01 Jan 2001 00:00:00 GMT"

        class _GNews:
            def __init__(self, *a, **k): pass
            def get_top_news(self):
                return [
                    {"url": "https://ex.com/today", "published date": today_str,
                     "publisher": {"title": "P"}, "title": "T1", "description": "", "score": 0.0},
                    {"url": "https://ex.com/old", "published date": older_str}
                ]

        with patch.object(gnews_mod, "GNews", _GNews):
            out = gnews_mod.get_all_top_gnews()

        self.assertEqual(len(out["data"]), 1)
        m = out["metrics"]
        # total_articles_fetched counts all seen items before date filtering
        self.assertEqual(m["total_articles_fetched"], 2)
        self.assertEqual(m["successful_scrapes"], 1)
        self.assertEqual(m["failed_scrapes"], 0)


# -----------------------------
# Tests for yfinance ingestion
# -----------------------------

class YFinanceIngestionTests(unittest.TestCase):
    def setUp(self):
        # NewsModel for duplicate checks (used by get_stock_news)
        self.news_patch = patch.object(yfin_mod, "NewsModel", _NewsModelStub)
        self.news_patch.start()

        # Helpers
        self.scrape_patch = patch.object(yfin_mod, "scrape_article", return_value="<html>ok</html>")
        self.details_patch = patch.object(yfin_mod, "get_article_details", return_value={
            "text": "body",
            "summary": "sum",
            "numerical_score": 0.2,
            "finbert_score": 0.1,
            "second_model_score": 0.3,
            "third_model_score": 0.05,
            "classification": "Neutral",
            "keywords": [],
            "confidence": 0.7,
            "agreement_rate": 0.8,
            "companies": ["AAPL"],
            "regions": ["US"],
            "sectors": ["Tech"],
        })
        self.quality_patch = patch.object(yfin_mod, "evaluate_scraping_quality", return_value={"is_clean": True})
        self.scrape_patch.start()
        self.details_patch.start()
        self.quality_patch.start()

    def tearDown(self):
        self.quality_patch.stop()
        self.details_patch.stop()
        self.scrape_patch.stop()
        self.news_patch.stop()
        _NewsModelStub.existing_urls.clear()

    def test_get_stock_price_reads_info(self):
        class _Ticker:
            @property
            def actions(self): return None
            @property
            def info(self): return {"currentPrice": 123.45}
        with patch.object(yfin_mod, "yf") as mock_yf:
            mock_yf.Ticker.return_value = _Ticker()
            price = yfin_mod.get_stock_price("AAPL")
        self.assertEqual(price, 123.45)

    def test_get_stock_history_various_periods(self):
        # Build small history DF
        idx = pd.date_range("2025-01-01", periods=3, freq="D")
        df = pd.DataFrame({"Close": [10.0, 12.0, 15.0]}, index=idx)

        class _Ticker:
            def history(self, *a, **k):
                # Return DF regardless of args
                return df

        with patch.object(yfin_mod, "yf") as mock_yf:
            mock_yf.Ticker.return_value = _Ticker()
            out_1y = yfin_mod.get_stock_history("AAPL", period="1y")
            out_1d = yfin_mod.get_stock_history("AAPL", period="1d")
            out_5d = yfin_mod.get_stock_history("AAPL", period="5d")
            out_ytd = yfin_mod.get_stock_history("AAPL", period="ytd")

        for out in (out_1y, out_1d, out_5d, out_ytd):
            self.assertIsInstance(out, dict)
            self.assertIn("dates", out)
            self.assertIn("prices", out)
            self.assertIn("performance", out)
            self.assertEqual(len(out["dates"]), 3)
            self.assertEqual(out["prices"], [10.0, 12.0, 15.0])
            # performance ((15-10)/10)*100 = 50
            self.assertAlmostEqual(out["performance"], 50.0, places=5)

    def test_get_stock_history_empty_df_returns_none(self):
        class _Ticker:
            def history(self, *a, **k):
                return pd.DataFrame()  # empty
        with patch.object(yfin_mod, "yf") as mock_yf:
            mock_yf.Ticker.return_value = _Ticker()
            out = yfin_mod.get_stock_history("AAPL", period="1y")
        self.assertIsNone(out)

    def test_get_stock_news_happy_path(self):
        now = int(datetime.datetime.utcnow().timestamp())
        items = [
            {
                "link": "https://yahoo.com/a",
                "providerPublishTime": now,
                "publisher": "Yahoo",
                "title": "A news",
            },
            {
                "link": "https://yahoo.com/b",
                "providerPublishTime": now,
                "publisher": "Yahoo",
                "title": "B news",
            },
        ]

        class _Search:
            def __init__(self, *a, **k):
                self.news = items

        with patch.object(yfin_mod, "yf") as mock_yf:
            mock_yf.Search.return_value = _Search()
            out = yfin_mod.get_stock_news("AAPL")

        self.assertEqual(len(out["data"]), 2)
        m = out["metrics"]
        self.assertEqual(m["total_articles_fetched"], 2)
        self.assertEqual(m["successful_scrapes"], 2)
        self.assertEqual(m["failed_scrapes"], 0)
        self.assertEqual(m["low_quality_skipped"], 0)

    def test_get_stock_news_duplicate_and_low_quality(self):
        now = int(datetime.datetime.utcnow().timestamp())
        items = [{"link": "https://yahoo.com/x", "providerPublishTime": now, "publisher": "Y", "title": "X"}]

        class _Search:
            def __init__(self, *a, **k):
                self.news = items

        # First: low quality path
        with patch.object(yfin_mod, "yf") as mock_yf, \
             patch.object(yfin_mod, "evaluate_scraping_quality", return_value={"is_clean": False}):
            mock_yf.Search.return_value = _Search()
            out1 = yfin_mod.get_stock_news("AAPL")
        self.assertEqual(out1["metrics"]["low_quality_skipped"], 1)
        self.assertEqual(out1["metrics"]["successful_scrapes"], 0)
        self.assertEqual(len(out1["data"]), 0)

        # Now: duplicate path
        _NewsModelStub.existing_urls.add("https://yahoo.com/x")
        with patch.object(yfin_mod, "yf") as mock_yf:
            mock_yf.Search.return_value = _Search()
            out2 = yfin_mod.get_stock_news("AAPL")
        # duplicate is skipped silently; total_articles increments
        self.assertEqual(out2["metrics"]["total_articles_fetched"], 1)
        self.assertEqual(out2["metrics"]["successful_scrapes"], 0)
        self.assertEqual(len(out2["data"]), 0)


if __name__ == "__main__":
    unittest.main()
