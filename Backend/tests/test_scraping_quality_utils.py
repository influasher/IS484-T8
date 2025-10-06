import unittest

try:
    from app.utils import scraping_quality as mod
except Exception:
    import scraping_quality as mod  # fallback

class ScrapingQualityUtilsTests(unittest.TestCase):
    def test_low_quality_article(self):
        raw_html = "<html>" + ("x" * 1000) + "</html>"
        details = {"text": "short"}
        out = mod.evaluate_scraping_quality("u", raw_html, details, min_text_len=200, min_ratio=0.2)
        self.assertFalse(out["is_clean"])
        self.assertGreater(out["raw_html_length"], 0)
        self.assertLess(out["text_length"], 200)

    def test_high_quality_article(self):
        text = "t" * 500
        raw_html = "<html>" + ("x" * 2000) + "</html>"
        details = {"text": text}
        out = mod.evaluate_scraping_quality("u", raw_html, details, min_text_len=200, min_ratio=0.1)
        self.assertTrue(out["is_clean"])
        self.assertEqual(out["text_length"], 500)

if __name__ == "__main__":
    unittest.main()
