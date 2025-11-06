import unittest
from unittest.mock import patch
import tempfile
import os
import uuid
from flask_jwt_extended import create_access_token
from tests.test_routes.setup_mock_db import test_db
from app.models import User
from app import db


class RecommendationsIntegrationTest(unittest.TestCase):
    """Integration tests for recommendations blueprint routes"""

    def _create_sample_entities(self):
        rm_user = User(
            id=uuid.uuid4(),
            username="rm1",
            email="rm@example.com",
            first_name="RM",
            last_name="User",
            role="RELATIONSHIP_MANAGER"
        )
        client_user = User(
            id=uuid.uuid4(),
            username="client1",
            email="client@example.com",
            first_name="Client",
            last_name="User",
            role="CLIENT",
            rm_id=rm_user.id
        )
        db.session.add_all([rm_user, client_user])
        db.session.commit()

        # JWT for RM
        self.rm_token = create_access_token(identity=str(rm_user.id))
        self.client_token = create_access_token(identity=str(client_user.id))

        return rm_user, client_user

    # ---------------------------
    # /client/<client_id>
    # ---------------------------
    @patch("app.routes.recommendations.get_client_recommendations")
    def test_get_recommendations_success(self, mock_recommendations):
        with test_db() as client:
            _, client_user = self._create_sample_entities()
            mock_recommendations.return_value = [{"symbol": "AAPL", "rating": "BUY"}]
            response = client.get(
                f"/api/recommendations/client/{client_user.id}",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(data["success"])
            self.assertEqual(data["count"], 1)
            mock_recommendations.assert_called_once_with(str(client_user.id), 10)

    def test_get_recommendations_unauthorized_client_access(self):
        """Clients cannot access recommendations"""
        with test_db() as client:
            _, client_user = self._create_sample_entities()
            response = client.get(
                f"/api/recommendations/client/{client_user.id}",
                headers={"Authorization": f"Bearer {self.client_token}"}
            )
            self.assertEqual(response.status_code, 401)
            data = response.get_json()
            self.assertIn("Access denied", data["error"])

    @patch("app.routes.recommendations.get_client_recommendations")
    def test_get_recommendations_client_not_found(self, mock_recommendations):
        with test_db() as client:
            rm_user = User(
                id=uuid.uuid4(),
                username="rm1",
                email="rm@example.com",
                first_name="RM",
                last_name="User",
                role="RELATIONSHIP_MANAGER"
            )
        
            db.session.add(rm_user)
            db.session.commit()

            # JWT for RM
            rm_token = create_access_token(identity=str(rm_user.id))

            response = client.get(
                f"/api/recommendations/client/{uuid.uuid4()}",
                headers={"Authorization": f"Bearer {rm_token}"}
            )
            self.assertEqual(response.status_code, 404)
            mock_recommendations.assert_not_called()

    # ---------------------------
    # /client/<client_id>/health
    # ---------------------------
    @patch("app.routes.recommendations.get_client_portfolio_health")
    def test_get_portfolio_health_success(self, mock_health):
        with test_db() as client:
            _, client_user = self._create_sample_entities()
            mock_health.return_value = {"score": 0.85, "status": "Healthy"}

            response = client.get(
                f"/api/recommendations/client/{client_user.id}/health",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(data["success"])
            self.assertEqual(data["health_data"]["status"], "Healthy")

    @patch("app.routes.recommendations.get_client_portfolio_health")
    def test_get_portfolio_health_error(self, mock_health):
        with test_db() as client:
            _, client_user = self._create_sample_entities()
            mock_health.return_value = {"error": "Portfolio not found"}

            response = client.get(
                f"/api/recommendations/client/{client_user.id}/health",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )
            data = response.get_json()

            self.assertFalse(data["success"])
            self.assertEqual(response.status_code, 404)

    # ---------------------------
    # /client/<client_id>/report
    # ---------------------------
    @patch("app.routes.recommendations.get_client_portfolio_health")
    @patch("app.routes.recommendations.get_client_recommendations")
    def test_get_comprehensive_report(self, mock_recommendations, mock_health):
        with test_db() as client:
            _, client_user = self._create_sample_entities()
            mock_recommendations.return_value = [{"symbol": "TSLA"}]
            mock_health.return_value = {"score": 0.92}

            response = client.get(
                f"/api/recommendations/client/{client_user.id}/report",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(data["success"])
            self.assertEqual(data["client_id"], str(client_user.id))
            self.assertIn("recommendations", data)
            self.assertIn("health_assessment", data)

    # ---------------------------
    # /client/<client_id>/pdf
    # ---------------------------
    @patch("app.routes.recommendations.generate_client_recommendation_report")
    def test_generate_pdf_success(self, mock_generate_pdf):
        with test_db() as client:
            _, client_user = self._create_sample_entities()
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = os.path.join(tmpdir, "test_report.pdf")
                with open(pdf_path, "w") as f:
                    f.write("dummy pdf content")

                mock_generate_pdf.return_value = pdf_path

                response = client.get(
                    f"/api/recommendations/client/{client_user.id}/pdf",
                    headers={"Authorization": f"Bearer {self.rm_token}"}
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "application/pdf")
                mock_generate_pdf.assert_called_once_with(str(client_user.id))

    @patch("app.routes.recommendations.generate_client_recommendation_report")
    def test_generate_pdf_failure(self, mock_generate_pdf):
        with test_db() as client:
            _, client_user = self._create_sample_entities()
            mock_generate_pdf.return_value = "/nonexistent/path/fake.pdf"

            response = client.get(
                f"/api/recommendations/client/{client_user.id}/pdf",
                headers={"Authorization": f"Bearer {self.rm_token}"}
            )

            data = response.get_json()
            self.assertEqual(response.status_code, 500)
            self.assertFalse(data["success"])
            self.assertIn("Failed to generate PDF", data["error"])

