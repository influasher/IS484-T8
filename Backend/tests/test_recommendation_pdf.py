import os
import uuid
import unittest
from unittest.mock import patch

# Import module under either layout
try:
    from app.services import recommendation_pdf as pdf_module
except Exception:
    import recommendation_pdf as pdf_module  # noqa: F401, F403


class FakeClient:
    def __init__(self, id_, email="client@example.com", first_name="Ada", last_name="Lovelace", is_client=True):
        self.id = id_
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self._is_client = is_client
    def is_client(self):
        return self._is_client


class FakeQueryGet:
    def __init__(self, value):
        self.value = value
    def get(self, _id):
        return self.value


class FakeFPDF:
    """Small FPDF stub that writes a file when output() is called."""
    def __init__(self, *a, **k):
        self.w = 210  # page width used by code
    def set_auto_page_break(self, *a, **k): pass
    def add_page(self, *a, **k): pass
    def set_font(self, *a, **k): pass
    def cell(self, *a, **k): pass
    def ln(self, *a, **k): pass
    def multi_cell(self, *a, **k): pass
    def set_text_color(self, *a, **k): pass
    def set_fill_color(self, *a, **k): pass
    def set_y(self, *a, **k): pass
    def output(self, path, _mode):
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4\n%fake\n%%EOF")


class RecommendationPDFTests(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(pdf_module.sanitize_text("café"), "cafe")     # remove accent
        self.assertEqual(pdf_module.get_risk_color("LOW"), (0, 200, 0))
        self.assertEqual(pdf_module.get_risk_color("HIGH"), (255, 0, 0))
        self.assertEqual(pdf_module.get_risk_color("???"), (128, 128, 128))
        self.assertEqual(pdf_module.get_sentiment_color(25), (0, 200, 0))
        self.assertEqual(pdf_module.get_sentiment_color(0), (255, 204, 0))
        self.assertEqual(pdf_module.get_sentiment_color(-30), (255, 0, 0))

    def test_generate_pdf_success_writes_file(self):
        cid = uuid.uuid4()
        client = FakeClient(cid)

        recs = [
            {"action": "BUY", "entity_name": "Acme", "ticker": "ACM",
             "recommendation_confidence": 0.8, "sentiment_score": 22.0,
             "risk_level": "LOW", "reasoning": "good"},
            {"action": "SELL", "entity_name": "Globex", "ticker": "GBX",
             "recommendation_confidence": 0.7, "sentiment_score": -30.0,
             "risk_level": "HIGH", "reasoning": "bearish"},
        ]
        health = {"overall_health_score": 75.2, "cash_analysis": {"available_cash": 1000}, "recommendations": ["Hold more cash"]}
        summary = {"total_portfolio_value": 12345.67}

        # monkeypatch: User.query.get, data services, and FPDF
        class FakeUserClass:
            query = FakeQueryGet(client)

        with patch.object(pdf_module, "User", FakeUserClass), \
             patch.object(pdf_module, "get_client_recommendations", return_value=recs), \
             patch.object(pdf_module, "get_client_portfolio_health", return_value=health), \
             patch.object(pdf_module, "get_client_portfolio_summary", return_value=summary), \
             patch.object(pdf_module, "FPDF", FakeFPDF):
            out = pdf_module.generate_recommendation_pdf(str(cid))

        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 8)
        # cleanup
        os.remove(out)

    def test_generate_pdf_raises_when_client_missing(self):
        class FakeUserClass:
            query = FakeQueryGet(None)
        with patch.object(pdf_module, "User", FakeUserClass):
            with self.assertRaises(ValueError):
                pdf_module.generate_recommendation_pdf(str(uuid.uuid4()))

    def test_generate_pdf_raises_when_not_client(self):
        cid = uuid.uuid4()
        class FakeUserClass:
            query = FakeQueryGet(FakeClient(cid, is_client=False))
        with patch.object(pdf_module, "User", FakeUserClass):
            with self.assertRaises(ValueError):
                pdf_module.generate_recommendation_pdf(str(cid))
