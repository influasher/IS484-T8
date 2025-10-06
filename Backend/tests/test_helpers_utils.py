import unittest
from flask import Flask

try:
    from app.utils import helpers as mod
except Exception:
    import helpers as mod  # fallback

class HelpersUtilsTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_format_response(self):
        resp, code = mod.format_response({"x": 1}, "ok", 201)
        self.assertEqual(code, 201)
        j = resp.get_json()
        self.assertEqual(j["status"], 201)
        self.assertEqual(j["message"], "ok")
        self.assertEqual(j["data"], {"x": 1})

    def test_calculate_percentage(self):
        self.assertEqual(mod.calculate_percentage(50, 200), 25)
        self.assertEqual(mod.calculate_percentage(1, 0), 0)

    def test_format_date_into_tuple_for_gnews(self):
        self.assertEqual(mod.format_date_into_tuple_for_gnews("2025-10-06"), (2025, 10, 6))

    def test_password_rule_checker(self):
        ok, _ = mod.password_rule_checker("GoodPass1!")
        self.assertTrue(ok)
        ok2, _ = mod.password_rule_checker("short")
        self.assertFalse(ok2)

if __name__ == "__main__":
    unittest.main()
