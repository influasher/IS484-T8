from flask import Blueprint, request
from app.services.sentiment_history_services import (
    get_sentiment_history_by_entity_id,
    create_sentiment_history,
)
from app.utils.helpers import format_response

sentiment_history_bp = Blueprint("sentiment_history", __name__)


# ** Get Sentiment History by Entity ID
@sentiment_history_bp.route("/", methods=["GET"])
def gethistory_by_entity_id():
    entity_id = request.args.get("entity_id", default=None, type=int)
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    sort_order = request.args.get("sort_order", default="desc", type=str)

    sentitment_history = get_sentiment_history_by_entity_id(
        entity_id, page, per_page, sort_order
    )

    if sentitment_history is None:
        return format_response([], "No sentiment history found", 404)

    return format_response(
        sentitment_history, "Sentiment history fetched successfully", 200
    )


# ** Create Sentiment History
@sentiment_history_bp.route("/", methods=["POST"])
def create_history():
    data = request.get_json()
    entity_id = data.get("entity_id")
    sentiment_score = data.get("sentiment_score")

    if not entity_id or not sentiment_score:
        return format_response([], "Missing required fields", 400)

    new_entry = create_sentiment_history(entity_id, sentiment_score)

    if new_entry is None:
        return format_response([], "Failed to create sentiment history", 500)

    return format_response(new_entry, "Sentiment history created successfully", 201)
