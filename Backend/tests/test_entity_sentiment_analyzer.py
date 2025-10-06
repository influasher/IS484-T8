import unittest
from datetime import datetime, timedelta

try:
    from app.services import entity_sentiment_analyzer as mod
except Exception:
    import entity_sentiment_analyzer as mod  # fallback


# --------- Lightweight fake SentimentAnalyzer to avoid model/API calls ---------

class _FakeSA:
    """Deterministic stub for SentimentAnalyzer used inside EntitySentimentAnalyzer."""

    def __init__(self):
        # Pretend both backends are already "loaded"
        self.gemini_client = object()
        self.openai_api_key = "x"

    # loaders are no-ops but keep the same signature/return
    def _load_gemini(self):
        self.gemini_client = object()
        return True

    def _load_openai(self):
        self.openai_api_key = "x"
        return True

    # Model stubs: use markers in text to shape outputs
    def analyze_with_finbert(self, text):
        t = (text or "").lower()
        if "bull" in t:
            return {"classification": "positive", "numerical_score": 0.5, "detailed_scores": {}}
        if "bear" in t:
            return {"classification": "negative", "numerical_score": -0.4, "detailed_scores": {}}
        return {"classification": "neutral", "numerical_score": 0.0, "detailed_scores": {}}

    def analyze_with_gemini(self, text):
        t = (text or "").lower()
        if "gem-" in t:
            return {"classification": "negative", "numerical_score": -0.6, "detailed_scores": {}}
        if "gem0" in t:
            return {"classification": "neutral", "numerical_score": 0.0, "detailed_scores": {}}
        return {"classification": "positive", "numerical_score": 0.4, "detailed_scores": {}}

    def analyze_with_openai(self, text):
        t = (text or "").lower()
        if "oai-" in t:
            return {"classification": "negative", "numerical_score": -0.2, "detailed_scores": {}}
        if "oai0" in t:
            return {"classification": "neutral", "numerical_score": 0.0, "detailed_scores": {}}
        return {"classification": "positive", "numerical_score": 0.3, "detailed_scores": {}}

    def weighted_integration(self, a, b):
        """Mirror the production algorithm’s behavior at a high level."""
        # base average on -1..1, then scale to -100..100
        base = (a["numerical_score"] + b["numerical_score"]) / 2.0
        agree = a["classification"] == b["classification"]
        diff = abs(a["numerical_score"] - b["numerical_score"])
        confidence = 1.0 if agree else max(0.0, 1.0 - diff)
        adjusted = base * confidence
        normalized = adjusted * 100.0
        if normalized > 10:
            cls = "bullish"
        elif normalized < -10:
            cls = "bearish"
        else:
            cls = "neutral"
        return {
            "numerical_score": normalized,
            "classification": cls,
            "models_agree": agree,
            "confidence": confidence,
            "model_scores": {"finbert": a["numerical_score"], "second_model": b["numerical_score"]},
        }


class EntitySentimentAnalyzerTests(unittest.TestCase):
    def setUp(self):
        # Keep originals we’ll patch
        self.orig_SA = mod.SentimentAnalyzer
        self.orig_sleep = mod.time.sleep
        self.orig_tqdm = mod.tqdm

        # Patch out heavy deps / rate limiting
        mod.SentimentAnalyzer = _FakeSA
        mod.time.sleep = lambda *a, **k: None
        mod.tqdm = lambda x, **k: x  # don't wrap

        # Create analyzer and intercept file writes
        self.esa = mod.EntitySentimentAnalyzer()
        self._saved = []
        self.esa._save_results = lambda filename, data: self._saved.append((filename, data))

    def tearDown(self):
        # Restore patches
        mod.SentimentAnalyzer = self.orig_SA
        mod.time.sleep = self.orig_sleep
        mod.tqdm = self.orig_tqdm

    # ---------------- analyze_article ----------------

    def test_analyze_article_finbert_only_no_disagreement(self):
        res = self.esa.analyze_article("Markets look bull today", run_all_models=False)
        self.assertIn("finbert", res["model_results"])
        self.assertNotIn("gemini", res["model_results"])
        self.assertNotIn("openai", res["model_results"])
        self.assertEqual(res["integrated_results"], {})
        self.assertFalse(res["disagreement"])
        self.assertEqual(self.esa.disagreement_stats["total_articles"], 1)
        self.assertEqual(self.esa.disagreement_stats["disagreement_count"], 0)

    def test_analyze_article_with_gemini_and_openai_disagreement(self):
        # FinBERT -> positive, Gemini -> negative (gem-), OpenAI -> positive
        res = self.esa.analyze_article("Strong earnings bull gem- oai+", run_all_models=True)

        # Integrated results present (FinBERT with both; and Gemini vs OpenAI as both present)
        self.assertIn("finbert_gemini", res["integrated_results"])
        self.assertIn("finbert_openai", res["integrated_results"])
        self.assertIn("gemini_openai", res["integrated_results"])

        # Disagreement detected and tracked
        self.assertTrue(res["disagreement"])
        self.assertIn("finbert_gemini", res["disagreement_models"])
        self.assertGreaterEqual(self.esa.disagreement_stats["disagreement_count"], 1)
        self.assertGreaterEqual(self.esa.disagreement_stats["disagreement_by_model"]["finbert_gemini"], 1)

        # Article logged
        self.assertGreaterEqual(len(self.esa.article_results), 1)

    # ---------------- analyze_corpus & summary ----------------

    def test_analyze_corpus_and_summary_saved(self):
        articles = [
            {"text": "bull gem+ oai+"},
            {"text": "bear gem0 oai-"},
            {"text": "neutral gem- oai+"},
        ]
        summary = self.esa.analyze_corpus(articles, run_all_models=True)

        # Two files saved: raw results + summary
        saved_names = [n for (n, _) in self._saved]
        self.assertIn("corpus_results.json", saved_names)
        self.assertIn("corpus_summary.json", saved_names)

        # Summary sanity
        self.assertEqual(summary["total_articles"], 3)
        # With our crafted inputs, there should be at least one disagreement
        self.assertGreaterEqual(summary["disagreement_count"], 1)
        # FinBERT count equals total; others should also be total since run_all_models=True
        self.assertEqual(summary["model_counts"]["finbert"], 3)
        self.assertEqual(summary["model_counts"]["gemini"], 3)
        self.assertEqual(summary["model_counts"]["openai"], 3)

        # Average scores are in the -1..1 range for the fake models
        self.assertTrue(-1.0 <= summary["avg_scores_by_model"]["finbert"] <= 1.0)
        self.assertTrue(-1.0 <= summary["avg_scores_by_model"]["gemini"] <= 1.0)
        self.assertTrue(-1.0 <= summary["avg_scores_by_model"]["openai"] <= 1.0)

    # ---------------- unified sentiment & weighting ----------------

    def test_generate_unified_sentiment_scores_conf_time_combined(self):
        # Provide pre-analyzed articles so we don't call analyze_article in this test
        now = datetime.now()
        articles = [
            {
                "text": "unused",
                "metadata": {"date": (now - timedelta(days=0)).isoformat(), "source": "s1"},
                "analysis": {
                    "integrated_results": {"finbert_gemini": {"numerical_score": 30.0, "confidence": 0.9}},
                    "model_results": {"finbert": {"score": 0.5}},  # fallback if needed
                },
            },
            {
                "text": "unused",
                "metadata": {"date": (now - timedelta(days=2)).isoformat(), "source": "s2"},
                "analysis": {
                    "integrated_results": {"finbert_gemini": {"numerical_score": 10.0, "confidence": 0.5}},
                    "model_results": {"finbert": {"score": 0.2}},
                },
            },
            {
                "text": "unused",
                "metadata": {"date": (now - timedelta(days=7)).isoformat(), "source": "s3"},
                "analysis": {
                    "integrated_results": {"finbert_gemini": {"numerical_score": -20.0, "confidence": 0.2}},
                    "model_results": {"finbert": {"score": -0.2}},
                },
            },
        ]

        weights = {"confidence": True, "time_decay": True, "decay_factor": 0.9, "preferred_method": "combined_weighted"}
        out = self.esa.generate_unified_sentiment_scores("ACME", articles, weights)

        # Shape and fields
        self.assertEqual(out["entity"], "ACME")
        self.assertIn("aggregation_methods", out)
        self.assertIn("simple_average", out["aggregation_methods"])
        self.assertIn("confidence_weighted", out["aggregation_methods"])
        self.assertIn("time_weighted", out["aggregation_methods"])
        self.assertIn("combined_weighted", out["aggregation_methods"])
        self.assertEqual(out["preferred_method"], "combined_weighted")

        # Values look sane
        self.assertEqual(out["article_count"], 3)
        self.assertEqual(len(out["scores"]), 3)
        self.assertEqual(len(out["confidences"]), 3)
        self.assertTrue(0.3 <= out["confidence"] <= 0.95)  # bounded confidence

        # Classification should follow the unified score sign
        if out["unified_score"] > 10:
            self.assertEqual(out["classification"], "bullish")
        elif out["unified_score"] < -10:
            self.assertEqual(out["classification"], "bearish")
        else:
            self.assertEqual(out["classification"], "neutral")

    def test_confidence_weighting_fallback_when_all_zero(self):
        now = datetime.now()
        # All confidences zero -> confidence_weighted must fall back to simple average
        articles = [
            {
                "text": "unused",
                "metadata": {"date": now.isoformat()},
                "analysis": {
                    "integrated_results": {"finbert_gemini": {"numerical_score": 40.0, "confidence": 0.0}},
                    "model_results": {"finbert": {"score": 0.4}},
                },
            },
            {
                "text": "unused",
                "metadata": {"date": now.isoformat()},
                "analysis": {
                    "integrated_results": {"finbert_gemini": {"numerical_score": -20.0, "confidence": 0.0}},
                    "model_results": {"finbert": {"score": -0.2}},
                },
            },
        ]

        out = self.esa.generate_unified_sentiment_scores(
            "OMEGA",
            articles,
            weights={"confidence": True, "time_decay": False, "preferred_method": "confidence_weighted"},
        )

        simple_avg = out["aggregation_methods"]["simple_average"]["score"]
        conf_avg = out["aggregation_methods"]["confidence_weighted"]["score"]
        self.assertAlmostEqual(simple_avg, conf_avg, places=5)  # fallback path hit


if __name__ == "__main__":
    unittest.main()
