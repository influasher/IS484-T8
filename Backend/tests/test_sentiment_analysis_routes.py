# import unittest
# import uuid
# from unittest.mock import patch, MagicMock
# from flask import Flask, json

# # Import the routes module under either layout
# try:
#     from app.routes import sentiment_analysis as routes_module
# except Exception:
#     import sentiment_analysis as routes_module  # fallback if flat layout

# # Determine patch target for EntitySentimentAnalyzer (imported inside route)
# ANALYZER_TARGET = (
#     "app.services.entity_sentiment_analyzer.EntitySentimentAnalyzer"
#     if routes_module.__name__.startswith("app.")
#     else "entity_sentiment_analyzer.EntitySentimentAnalyzer"
# )

# # -------------------- Helpers / Fakes --------------------

# def fake_format_response(data, message, status):
#     # Make response predictable for assertions
#     return {"data": data, "message": message, "status": status}, status


# class _QueryAll:
#     def __init__(self, items):
#         self._items = items
#     def all(self):
#         return self._items


# class _FakeEntity:
#     def __init__(self, name, ticker):
#         self.id = uuid.uuid4()
#         self.name = name
#         self.ticker = ticker


# class _FakeAnalyzer:
#     def __init__(self, result):
#         self._result = result
#     def generate_unified_sentiment_scores(self, entity_name, articles, weights):
#         # Return prearranged result used by the route
#         return self._result


# # -------------------- Test Case --------------------

# class SentimentRoutesTestCase(unittest.TestCase):

#     def setUp(self):
#         self.app = Flask(__name__)
#         self.app.config["TESTING"] = True

#         # Register blueprint only once
#         if "sentiment" not in self.app.blueprints:
#             self.app.register_blueprint(routes_module.sentiment_bp, url_prefix="/sentiment")

#         self.client = self.app.test_client()
#         self.ctx = self.app.app_context()
#         self.ctx.push()

#         # Patch format_response at the module level for clean assertions
#         self._fmt_patch = patch.object(routes_module, "format_response", side_effect=fake_format_response)
#         self._fmt_patch.start()

#     def tearDown(self):
#         self._fmt_patch.stop()
#         self.ctx.pop()

#     # -------------------- /sentiment/analyze --------------------

#     def test_analyze_calls_get_sentiment_and_returns_200(self):
#         with patch.object(routes_module, "get_sentiment", return_value={"s": 1}) as mock_get:
#             resp = self.client.post("/sentiment/analyze", json={"text": "hello world"})
#         self.assertEqual(resp.status_code, 200)
#         body = resp.get_json()
#         self.assertEqual(body["message"], "Sentiment analysis successful")
#         self.assertEqual(body["data"], {"s": 1})
#         # Ensure it was called with (text, False)
#         mock_get.assert_called_once_with("hello world", False)

#     def test_analyze_defaults_to_empty_text_when_missing(self):
#         with patch.object(routes_module, "get_sentiment", return_value={"ok": True}) as mock_get:
#             resp = self.client.post("/sentiment/analyze", json={})
#         self.assertEqual(resp.status_code, 200)
#         body = resp.get_json()
#         self.assertEqual(body["message"], "Sentiment analysis successful")
#         self.assertEqual(body["data"], {"ok": True})
#         mock_get.assert_called_once_with("", False)

#     # -------------------- /sentiment/entity --------------------

#     def test_analyze_entity_no_entities_returns_empty(self):
#         # Entity.query.all() -> []
#         class _EntityClass:
#             query = _QueryAll(items=[])
#         with patch.object(routes_module, "Entity", _EntityClass):
#             resp = self.client.post("/sentiment/entity", json={})
#         self.assertEqual(resp.status_code, 200)
#         body = resp.get_json()
#         self.assertEqual(body["message"], "Sentiment analysis for entities successful")
#         self.assertEqual(body["data"], [])

#     def test_analyze_entity_skips_when_no_news(self):
#         # One entity, but news_by_ticker returns falsy -> skips
#         e = _FakeEntity("Acme Corp", "ACM")
#         class _EntityClass:
#             query = _QueryAll(items=[e])

#         with patch.object(routes_module, "Entity", _EntityClass), \
#              patch.object(routes_module, "news_by_ticker", return_value=None), \
#              patch.object(routes_module, "create_sentiment_history") as mock_hist, \
#              patch.object(routes_module, "update_entity_sentiment") as mock_upd:
#             resp = self.client.post("/sentiment/entity", json={})

#         self.assertEqual(resp.status_code, 200)
#         body = resp.get_json()
#         # No items added (skipped due to no news)
#         self.assertEqual(body["data"], [])
#         mock_hist.assert_not_called()
#         mock_upd.assert_not_called()

#     def test_analyze_entity_happy_path_with_news_dict(self):
#         # Two entities: first returns dict with "news", second returns list (covered in another test)
#         e = _FakeEntity("Globex", "GBX")

#         class _EntityClass:
#             query = _QueryAll(items=[e])

#         news_items = [
#             {
#                 "summary": "Strong quarter for GBX",
#                 "publisher": "BizNews",
#                 "published_date": "2025-01-01",
#                 "title": "GBX beats estimates",
#             },
#             {
#                 "summary": "Guidance raised for next year",
#                 "publisher": "Markets",
#                 "published_date": "2025-01-02",
#                 "title": "GBX outlook positive",
#             },
#         ]

#         # Analyzer’s unified result (values convertible to float)
#         unified = {
#             "unified_score": 0.35,
#             "aggregation_methods": {
#                 "confidence_weighted": {"score": 0.40},
#                 "time_weighted": {"score": 0.33},
#                 "simple_average": {"score": 0.36},
#             },
#             "classification": "bullish",
#         }

#         with patch.object(routes_module, "Entity", _EntityClass), \
#              patch.object(routes_module, "news_by_ticker", return_value={"news": news_items}), \
#              patch.object(routes_module, "create_sentiment_history", return_value={"saved": True}) as mock_hist, \
#              patch.object(routes_module, "update_entity_sentiment", return_value=True) as mock_upd, \
#              patch(ANALYZER_TARGET, return_value=_FakeAnalyzer(unified)):
#             resp = self.client.post("/sentiment/entity", json={})

#         self.assertEqual(resp.status_code, 200)
#         body = resp.get_json()
#         self.assertEqual(body["message"], "Sentiment analysis for entities successful")
#         self.assertEqual(len(body["data"]), 1)
#         item = body["data"][0]
#         self.assertEqual(item["entity_name"], e.name)
#         self.assertEqual(item["classification"], "bullish")
#         # Ensure side-effects invoked with correct args
#         mock_hist.assert_called_once()
#         mock_upd.assert_called_once()
#         args, kwargs = mock_upd.call_args
#         self.assertEqual(kwargs["ticker"], e.ticker)
#         self.assertAlmostEqual(kwargs["sentiment_score"], 0.35, places=5)
#         self.assertAlmostEqual(kwargs["confidence_score"], 0.40, places=5)
#         self.assertAlmostEqual(kwargs["time_decay_score"], 0.33, places=5)
#         self.assertAlmostEqual(kwargs["simple_average_score"], 0.36, places=5)
#         self.assertEqual(kwargs["classification"], "bullish")

#     def test_analyze_entity_happy_path_with_news_list(self):
#         e = _FakeEntity("Initech", "INT")
#         class _EntityClass:
#             query = _QueryAll(items=[e])

#         news_items = [
#             {
#                 "summary": "INT launches product",
#                 "publisher": "TechWire",
#                 "published_date": "2025-02-01",
#                 "title": "Initech expands lineup",
#             }
#         ]

#         unified = {
#             "unified_score": -0.12,
#             "aggregation_methods": {
#                 "confidence_weighted": {"score": -0.10},
#                 "time_weighted": {"score": -0.11},
#                 "simple_average": {"score": -0.12},
#             },
#             "classification": "bearish",
#         }

#         with patch.object(routes_module, "Entity", _EntityClass), \
#              patch.object(routes_module, "news_by_ticker", return_value=news_items), \
#              patch.object(routes_module, "create_sentiment_history", return_value={"saved": True}) as mock_hist, \
#              patch.object(routes_module, "update_entity_sentiment", return_value=True) as mock_upd, \
#              patch(ANALYZER_TARGET, return_value=_FakeAnalyzer(unified)):
#             resp = self.client.post("/sentiment/entity", json={})

#         self.assertEqual(resp.status_code, 200)
#         body = resp.get_json()
#         self.assertEqual(len(body["data"]), 1)
#         item = body["data"][0]
#         self.assertEqual(item["entity_name"], e.name)
#         self.assertEqual(item["classification"], "bearish")
#         mock_hist.assert_called_once()
#         mock_upd.assert_called_once()

#     def test_analyze_entity_update_returns_false_not_appended(self):
#         e = _FakeEntity("Hooli", "HLI")
#         class _EntityClass:
#             query = _QueryAll(items=[e])

#         news_items = [
#             {"summary": "Neutral quarter", "publisher": "FinDaily", "published_date": "2025-03-01", "title": "HLI Q1"},
#         ]
#         unified = {
#             "unified_score": 0.0,
#             "aggregation_methods": {
#                 "confidence_weighted": {"score": 0.0},
#                 "time_weighted": {"score": 0.0},
#                 "simple_average": {"score": 0.0},
#             },
#             "classification": "neutral",
#         }

#         with patch.object(routes_module, "Entity", _EntityClass), \
#              patch.object(routes_module, "news_by_ticker", return_value={"news": news_items}), \
#              patch.object(routes_module, "create_sentiment_history", return_value={"saved": True}) as mock_hist, \
#              patch.object(routes_module, "update_entity_sentiment", return_value=False) as mock_upd, \
#              patch(ANALYZER_TARGET, return_value=_FakeAnalyzer(unified)):
#             resp = self.client.post("/sentiment/entity", json={})

#         self.assertEqual(resp.status_code, 200)
#         body = resp.get_json()
#         # Since update returned False, result should not include the entity
#         self.assertEqual(body["data"], [])
#         mock_hist.assert_called_once()
#         mock_upd.assert_called_once()


# if __name__ == "__main__":
#     unittest.main()
