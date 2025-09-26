from flask import request, Blueprint
from flask_mail import Mail
from datetime import datetime
from app.services.export_pdf import generate_pdf
from app.services.email_pdf import send_email_with_attachment
from app.services.news_services import news_by_ticker
from app.services.entities_service import (
    get_ticker_by_entity,
    get_entity_details,
    get_id_by_entity,
)
from app.services.sentiment_history_services import get_sentiment_history_by_entity_id
from app.utils.helpers import format_response
import os
import logging
import traceback
import threading
import time
from dotenv import load_dotenv

load_dotenv()

send_pdf_bp = Blueprint("send_pdf_email", __name__)
mail = Mail()  # Initialize Flask-Mail


@send_pdf_bp.route("/send_pdf_email", methods=["POST"])
def send_pdf_email():
    try:
        data = request.get_json()
        entity_name = data.get("entity_name")
        entity_id = get_id_by_entity(entity_name)
        ticker = get_ticker_by_entity(entity_name)
        sender_email = (
            "eileenlee31@gmail.com"  # TODO: Need to use the actual email from JSON
        )
        recipient_email = (
            "rabbitboi0911@gmail.com"  # TODO: Need to use the actual email from JSON
        )

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

        email_sent = send_email_with_attachment(
            mail, pdf_filepath, recipient_email, sender_email, entity_name
        )

        if not email_sent:
            return format_response(None, "Failed to send email", 500)

        # Delete the PDF file after sending
        def cleanup():
            time.sleep(5)  # Give time for the file to be fully sent
            try:
                if os.path.exists(pdf_filepath):
                    os.remove(pdf_filepath)
                    logging.info(f"Deleted file: {pdf_filepath}")
            except Exception:
                logging.error(f"Error deleting file: {traceback.format_exc()}")

        # Run cleanup in a background thread
        threading.Thread(target=cleanup, daemon=True).start()
        return format_response({"success": True}, "Email sent", 200)

    except Exception:
        logging.error(f"Error: {traceback.format_exc()}")
        return format_response(None, "Failed to send email", 500)
