from flask import request, send_file, Blueprint
import os
import time
from datetime import datetime
import logging
import traceback
from app.services.export_pdf import generate_pdf
from app.services.news_services import news_by_ticker
from app.services.entities_service import (
    get_ticker_by_entity,
    get_entity_details,
    get_id_by_entity,
)
from app.services.sentiment_history_services import get_sentiment_history_by_entity_id
from app.utils.helpers import format_response
import threading

pdf_bp = Blueprint("pdf", __name__)

UPLOAD_FOLDER = "temp_pdfs"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@pdf_bp.route("/generate-pdf", methods=["POST"])
def export_pdf():
    data = request.get_json()
    entity_name = data.get("entity_name")
    entity_id = get_id_by_entity(entity_name)
    ticker = get_ticker_by_entity(entity_name)

    if not entity_name or not ticker:
        return format_response(None, "Missing required fields", 400)

    # Fetch data for the report
    news_items = news_by_ticker(
        ticker, page=1, per_page=5, sort_order="desc", filter_time="24"
    )

    if not news_items:
        # fallback to 'all' if no news in the past 24 hours
        news_items = news_by_ticker(
            ticker, page=1, per_page=10, sort_order="desc", filter_time="all"
        )

    # Fetch entity data
    entity_scores = get_entity_details(ticker)
    if not entity_scores:
        return format_response(None, "No entity scores found", 401)

    sentiment_history = get_sentiment_history_by_entity_id(
        entity_id, page=1, per_page=5, sort_order="desc"
    )
    if not sentiment_history:
        return format_response(None, "No sentiment history found", 402)

    # Generate PDF
    output_filename = (
        f"{entity_name}_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    )
    pdf_filepath = generate_pdf(
        entity_name, entity_scores, sentiment_history, news_items, output_filename
    )

    base_path = os.getcwd()  # Get the current working directory
    pdf_filepath = os.path.join(base_path, "temp_pdfs", output_filename)

    logging.info(f"Generated PDF path: {pdf_filepath}")

    # Ensure the file exists before sending
    if not os.path.exists(pdf_filepath):
        logging.error(f"File not found: {pdf_filepath}")
        return format_response(None, "Failed to generate report", 500)

    def cleanup():
        time.sleep(5)  # Give time for the file to be fully sent
        try:
            if os.path.exists(pdf_filepath):
                os.remove(pdf_filepath)
                logging.info(f"Deleted file: {pdf_filepath}")
        except Exception as e:
            logging.error(f"Error deleting file: {traceback.format_exc()}")

    try:
        response = send_file(
            pdf_filepath, as_attachment=True, mimetype="application/pdf"
        )

        # Run cleanup in a background thread
        threading.Thread(target=cleanup, daemon=True).start()
        return response
    except Exception as e:
        logging.error(f"Error sending PDF: {traceback.format_exc()}")
        return format_response(None, "Error generating PDF", 500)
