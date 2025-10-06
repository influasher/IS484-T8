import os
import unittest
import pandas as pd
from datetime import datetime, timedelta

try:
    from app.services import export_pdf as mod
except Exception:
    import export_pdf as mod  # fallback

class ExportPdfTests(unittest.TestCase):
    def setUp(self):
        # Patch yf.Ticker to return predictable history
        class _Ticker:
            def history(self, period="1mo"):
                idx = pd.date_range(datetime.now() - timedelta(days=9), periods=10, freq="D")
                return pd.DataFrame({"Close": [100 + i for i in range(10)]}, index=idx)
        self._orig_yf = mod.yf
        class _YF: Ticker = staticmethod(lambda t: _Ticker())
        mod.yf = _YF

    def tearDown(self):
        mod.yf = self._orig_yf

    def test_generate_pdf_creates_file(self):
        entity_name = "ACME"
        entity_scores = {
            "ticker": "ACME",
            "classification": "bullish",
            "avg_score": 12.34,
            "simple_average": 10.0,
            "time_decay": 8.0,
        }
        sentiment_history = {
            "sentiment_history": [
                {"sentiment_score": 5, "date": datetime.now() - timedelta(days=2)},
                {"sentiment_score": -3, "date": datetime.now() - timedelta(days=1)},
            ]
        }
        news_items = {
            "news": [
                {"title": "A", "summary": "S", "publisher": "P", "published_date": "2025-01-01", "url": "u", "sentiment":"positive","score":0.2, "regions":["US"], "sectors":["Tech"]},
            ]
        }
        out_path = mod.generate_pdf(entity_name, entity_scores, sentiment_history, news_items, output_filename="test_report.pdf")
        try:
            self.assertTrue(os.path.isfile(out_path))
        finally:
            # Cleanup
            if os.path.exists(out_path):
                os.remove(out_path)
