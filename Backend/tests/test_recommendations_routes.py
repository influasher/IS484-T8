import os
import uuid
import unittest
from unittest.mock import patch

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

# Import module under either layout
try:
    from app.routes import recommendations as recs_module
except Exception:
    import recommendations as recs_module  # noqa: F401, F403


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["JWT_SECRET_KEY"] = "test-secret"
        JWTManager(self.app)

        if "recommendations" not in self.app.blueprints:
            self.app.register_blueprint(recs_module.recommendations_bp, url_prefix="/recommendations")

        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def auth_headers(self, identity=None):
        if identity is None:
            identity = uuid.uuid4()
        if isinstance(identity, uuid.UUID):
            identity = str(identity)
        with self.app.app_context():
            token = create_access_token(identity=identity)
        return {"Authorization": f"Bearer {token}"}


class RecommendationsRoutesTest(BaseTestCase):
    # ---------------- GET /client/<id> ----------------

    def test_get_recommendations_requires_auth_401(self):
        cid = uuid.uuid4()
        resp = self.client.get(f"/recommendations/client/{cid}")
        self.assertEqual(resp.status_code, 401)

    def test_get_recommendations_access_denied_401(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(None, "Access denied. Only Relationship Managers can access client data.")):
            resp = self.client.get(f"/recommendations/client/{cid}", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Access denied", resp.get_json()["error"])

    def test_get_recommendations_client_not_found_404(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(None, "Client not found")):
            resp = self.client.get(f"/recommendations/client/{cid}", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 404)

    def test_get_recommendations_invalid_uuid_404(self):
        bad = "not-a-uuid"
        with patch.object(recs_module, "check_client_access", return_value=(None, "Invalid client ID format")):
            resp = self.client.get(f"/recommendations/client/{bad}", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Invalid client ID format", resp.get_json()["error"])

    def test_get_recommendations_success_uses_limit_and_default(self):
        cid = uuid.uuid4()
        fake_client = object()
        with patch.object(recs_module, "check_client_access", return_value=(fake_client, None)), \
             patch.object(recs_module, "get_client_recommendations", return_value=[{"x": 1}, {"x": 2}]) as mock_get:
            # explicit limit
            r1 = self.client.get(f"/recommendations/client/{cid}?limit=5", headers=self.auth_headers())
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(r1.get_json()["count"], 2)
            called_id, called_limit = mock_get.call_args[0]
            self.assertEqual(called_id, str(cid))
            self.assertEqual(called_limit, 5)

            # default limit = 10
            r2 = self.client.get(f"/recommendations/client/{cid}", headers=self.auth_headers())
            self.assertEqual(r2.status_code, 200)
            called_id2, called_limit2 = mock_get.call_args[0]
            self.assertEqual(called_id2, str(cid))
            self.assertEqual(called_limit2, 10)

    def test_get_recommendations_unexpected_exception_500(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "get_client_recommendations", side_effect=RuntimeError("kaboom")):
            resp = self.client.get(f"/recommendations/client/{cid}", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 500)
        self.assertIn("kaboom", resp.get_json()["error"])

    # ------------- GET /client/<id>/health -------------

    def test_get_portfolio_health_access_denied_401(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(None, "Access denied. You can only access data for your own clients.")):
            resp = self.client.get(f"/recommendations/client/{cid}/health", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 401)

    def test_get_portfolio_health_not_found_404(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(None, "Client not found")):
            resp = self.client.get(f"/recommendations/client/{cid}/health", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 404)

    def test_get_portfolio_health_service_error_404(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "get_client_portfolio_health", return_value={"error": "No portfolio"}):
            resp = self.client.get(f"/recommendations/client/{cid}/health", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 404)

    def test_get_portfolio_health_success_200(self):
        cid = uuid.uuid4()
        health = {"overall_health_score": 76.5, "cash_analysis": {"available_cash": 999}}
        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "get_client_portfolio_health", return_value=health):
            resp = self.client.get(f"/recommendations/client/{cid}/health", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["health_data"], health)

    # ------------- GET /client/<id>/report -------------

    def test_get_report_access_denied_401(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(None, "Access denied. Only Relationship Managers can access client data.")):
            resp = self.client.get(f"/recommendations/client/{cid}/report", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 401)

    def test_get_report_health_error_404(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "get_client_recommendations", return_value=[{"ticker": "TSLA", "action": "BUY"}]), \
             patch.object(recs_module, "get_client_portfolio_health", return_value={"error": "Unavailable"}):
            resp = self.client.get(f"/recommendations/client/{cid}/report", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 404)

    def test_get_report_success_200(self):
        cid = uuid.uuid4()
        recs = [{"ticker": "NVDA", "action": "BUY"}]
        health = {"overall_health_score": 88.2}
        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "get_client_recommendations", return_value=recs), \
             patch.object(recs_module, "get_client_portfolio_health", return_value=health):
            resp = self.client.get(f"/recommendations/client/{cid}/report?limit=3", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["recommendations"], recs)
        self.assertEqual(data["health_assessment"], health)
        self.assertIsNone(data["generated_at"])

    # ---------------- GET /client/<id>/pdf ----------------

    def test_get_pdf_access_denied_401(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(None, "Access denied. You can only access data for your own clients.")):
            resp = self.client.get(f"/recommendations/client/{cid}/pdf", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 401)

    def test_get_pdf_missing_file_500(self):
        cid = uuid.uuid4()
        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "generate_client_recommendation_report", return_value="Z:/nope/does_not_exist.pdf"):
            resp = self.client.get(f"/recommendations/client/{cid}/pdf", headers=self.auth_headers())
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Failed to generate PDF", resp.get_json()["error"])

    def test_get_pdf_success_200_and_cleanup_thread_started(self):
        cid = uuid.uuid4()
        # create a tiny PDF on disk
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.write(fd, b"%PDF-1.4\n%ok\n%%EOF")
        os.close(fd)

        started = {"flag": False}

        class DummyThread:
            def __init__(self, target=None, daemon=None):
                self.target = target
                self.daemon = daemon
            def start(self):
                started["flag"] = True

        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "generate_client_recommendation_report", return_value=path), \
             patch.object(recs_module.threading, "Thread", side_effect=lambda *a, **k: DummyThread(*a, **k)):
            resp = self.client.get(f"/recommendations/client/{cid}/pdf", headers=self.auth_headers())

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers.get("Content-Type", "").startswith("application/pdf"))
        self.assertTrue(started["flag"])

    def test_get_pdf_send_file_raises_cleans_up_and_500(self):
        cid = uuid.uuid4()
        # make file to be cleaned if send_file fails
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.write(fd, b"%PDF-1.4\n%bad\n%%EOF")
        os.close(fd)

        with patch.object(recs_module, "check_client_access", return_value=(object(), None)), \
             patch.object(recs_module, "generate_client_recommendation_report", return_value=path), \
             patch.object(recs_module, "send_file", side_effect=RuntimeError("send-failed")):
            resp = self.client.get(f"/recommendations/client/{cid}/pdf", headers=self.auth_headers())

        self.assertEqual(resp.status_code, 500)
        # file cleaned up in except:
        self.assertFalse(os.path.exists(path))
