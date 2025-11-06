import unittest
from unittest.mock import patch
from datetime import datetime
import os
from tests.test_routes.setup_mock_db import test_db
from app.models import Entity, User
from app import db
import uuid
import shutil


class PDFIntegrationTest(unittest.TestCase):
    def _create_sample_entities(self):
        """Helper to seed test DB with sample entities."""
        entities = [
            Entity(
                id=uuid.uuid4(),
                name="Alpha Corp",
                ticker="ALPHA",
                sentiment_score=0.7,
                classification="bullish",
                asset_type="stock",
                sector=["Technology"],
            ),
            Entity(
                id=uuid.uuid4(),
                name="Beta LLC",
                ticker="BETA",
                sentiment_score=-0.3,
                classification="bearish",
                asset_type="bond",
                sector=["Finance"],
            ),
            Entity(
                id=uuid.uuid4(),
                name="Gamma Inc",
                ticker="GAMMA",
                sentiment_score=0.1,
                classification="neutral",
                asset_type="etf",
                sector=["Energy"],
            ),
        ]

        rm = User(
                id=uuid.uuid4(),           
                username="tom123",          # must not be None
                email="tom@example.com",
                first_name="Tom",
                last_name="Tim",
                role="RELATIONSHIP_MANAGER",                  
                rm_id=None                    
            )
        db.session.add_all(entities)
        db.session.add(rm)
        db.session.commit()
  
        self.entity = entities[0]
        self.entity_id = entities[0].id
        
    
    @patch("app.routes.pdf.get_ticker_by_entity")
    @patch("app.routes.pdf.get_id_by_entity")
    @patch("app.routes.pdf.news_by_ticker")
    @patch("app.routes.pdf.get_entity_details")
    @patch("app.routes.pdf.get_sentiment_history_by_entity_id")
    @patch("app.routes.pdf.generate_pdf")
    def test_generate_pdf_success(
        self, mock_generate_pdf, mock_sentiment, mock_entity, mock_news, mock_id, mock_ticker
    ):
        """Test successful PDF generation."""
        with test_db() as client:
            self._create_sample_entities()
            fixed_time = datetime(2025, 10, 31, 0, 58, 11)
            with patch("app.routes.pdf.datetime") as mock_datetime:
                mock_datetime.now.return_value = fixed_time
                mock_datetime.strftime = datetime.strftime  # keep strftime working

                pdf_path = os.path.join("temp_pdfs", f"{self.entity.name}_report_{fixed_time.strftime('%Y%m%d%H%M%S')}.pdf")
                os.makedirs("temp_pdfs", exist_ok=True)

                # Create dummy PDF at the path route expects
                with open(pdf_path, "wb") as f:
                    f.write(b"%PDF-1.4\n%Dummy PDF content")

                response = client.post(
                    "/api/pdf/generate-pdf",
                    json={"entity_name": self.entity.name}
                )

                assert response.status_code == 200
                assert response.content_type == "application/pdf"
                assert len(response.data) > 0
                
                # Cleanup
                pdf_dir = "temp_pdfs"
                if os.path.exists(pdf_dir):
                    shutil.rmtree(pdf_dir)

    @patch("app.routes.pdf.get_ticker_by_entity")
    @patch("app.routes.pdf.get_id_by_entity")
    def test_generate_pdf_missing_fields(self, mock_id, mock_ticker):
        """Test PDF generation fails when entity_name is missing."""
        with test_db() as client:
            response = client.post(
                "/api/pdf/generate-pdf",
                json={}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 400)
            self.assertEqual(data["message"], "Missing required fields")

    @patch("app.routes.pdf.get_ticker_by_entity")
    @patch("app.routes.pdf.get_id_by_entity")
    @patch("app.routes.pdf.news_by_ticker")
    @patch("app.routes.pdf.get_entity_details")
    @patch("app.routes.pdf.get_sentiment_history_by_entity_id")
    @patch("app.routes.pdf.generate_pdf")
    def test_generate_pdf_file_missing(
        self, mock_generate_pdf, mock_sentiment, mock_entity, mock_news, mock_id, mock_ticker
    ):
        """Test PDF generation fails if generate_pdf returns a non-existent file."""
        with test_db() as client:
            self._create_sample_entities()
            mock_ticker.return_value = self.entity.ticker
            mock_id.return_value = self.entity_id
            mock_news.return_value = [{"title": "Test News"}]
            mock_entity.return_value = {"score": 0.9}
            mock_sentiment.return_value = [{"date": "2025-10-31", "sentiment": 0.8}]
            mock_generate_pdf.return_value = "/non_existent_path/Test_Report.pdf"

            response = client.post(
                "/api/pdf/generate-pdf",
                json={"entity_name": self.entity.name}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 500)
            self.assertEqual(data["message"], "Failed to generate report")

    @patch("app.routes.pdf.get_ticker_by_entity")
    @patch("app.routes.pdf.get_id_by_entity")
    @patch("app.routes.pdf.news_by_ticker")
    @patch("app.routes.pdf.get_entity_details")
    @patch("app.routes.pdf.get_sentiment_history_by_entity_id")
    def test_generate_pdf_no_entity_scores(
        self, mock_sentiment, mock_entity, mock_news, mock_id, mock_ticker
    ):
        """Test PDF generation fails when no entity scores are found."""
        with test_db() as client:
            self._create_sample_entities()
            mock_ticker.return_value = self.entity.ticker
            mock_id.return_value = self.entity_id
            mock_news.return_value = [{"title": "Test News"}]
            mock_entity.return_value = None
            mock_sentiment.return_value = [{"date": "2025-10-31", "sentiment": 0.8}]

            response = client.post(
                "/api/pdf/generate-pdf",
                json={"entity_name": self.entity.name}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 401)
            self.assertEqual(data["message"], "No entity scores found")

    @patch("app.routes.pdf.get_ticker_by_entity")
    @patch("app.routes.pdf.get_id_by_entity")
    @patch("app.routes.pdf.news_by_ticker")
    @patch("app.routes.pdf.get_entity_details")
    @patch("app.routes.pdf.get_sentiment_history_by_entity_id")
    def test_generate_pdf_no_sentiment_history(
        self, mock_sentiment, mock_entity, mock_news, mock_id, mock_ticker
    ):
        """Test PDF generation fails when no sentiment history is found."""
        with test_db() as client:
            self._create_sample_entities()
            mock_ticker.return_value = self.entity.ticker
            mock_id.return_value = self.entity_id
            mock_news.return_value = [{"title": "Test News"}]
            mock_entity.return_value = {"score": 0.9}
            mock_sentiment.return_value = []

            response = client.post(
                "/api/pdf/generate-pdf",
                json={"entity_name": self.entity.name}
            )
            data = response.get_json()
            self.assertEqual(response.status_code, 402)
            self.assertEqual(data["message"], "No sentiment history found")

