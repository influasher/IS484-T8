from flask import Blueprint, jsonify
from app.utils.helpers import format_response

sentiment_bp = Blueprint("sentiment", __name__)


@sentiment_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    DEPRECATED: On-demand sentiment analysis has been moved to the News Processor microservice.
    Sentiment analysis now runs as a scheduled batch job (CronJob) every 2 days.
    
    To get sentiment scores, use:
    - GET /sentiment_history/ - Get historical sentiment scores by entity
    - GET /entities/<ticker> - Get entity details including current sentiment score
    """
    return format_response(
        {
            "message": "This endpoint is deprecated. Sentiment analysis is now handled by the News Processor microservice.",
            "alternatives": [
                "GET /sentiment_history/?entity_id=<entity_id> - Get sentiment history",
                "GET /entities/<ticker> - Get entity with current sentiment score"
            ]
        },
        "Endpoint deprecated",
        410  # 410 Gone - indicates the resource is no longer available
    )


@sentiment_bp.route("/entity", methods=["POST"])
def analyze_entity():
    """
    DEPRECATED: Entity sentiment analysis has been moved to the News Processor microservice.
    Entity sentiment is now calculated automatically during the scheduled news processing job.
    
    To get entity sentiment scores, use:
    - GET /entities/<ticker> - Get entity details including current sentiment score
    - GET /sentiment_history/?entity_id=<entity_id> - Get historical sentiment data
    """
    return format_response(
        {
            "message": "This endpoint is deprecated. Entity sentiment analysis is now handled by the News Processor microservice.",
            "alternatives": [
                "GET /entities/<ticker> - Get entity with current sentiment score",
                "GET /sentiment_history/?entity_id=<entity_id> - Get sentiment history"
            ]
        },
        "Endpoint deprecated",
        410  # 410 Gone
    )

