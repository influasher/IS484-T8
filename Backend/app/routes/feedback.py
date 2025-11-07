from flask import Blueprint, request
from app.models.feedback import Feedback
from app.services.feedback_services import (
    insert_feedback,
    get_feedback_by_userID,
    get_feedback_by_newsID,
    get_feedback_by_userID_and_newsID,
)
from app.utils.helpers import format_response

feedback_bp = Blueprint("feedback", __name__)


# ** Get Feedback by User ID
@feedback_bp.route("/user/<uuid:userID>", methods=["GET"])
def get_feedback_by_user(userID):
    feedback = get_feedback_by_userID(userID)
    if not feedback:
        return format_response(None, "Feedback not found", 404)
    return format_response(feedback, "Feedback fetched successfully", 200)


# ** Get Feedback by News ID
@feedback_bp.route("/news/<uuid:newsID>", methods=["GET"])
def get_feedback_by_news(newsID):
    feedback = get_feedback_by_newsID(newsID)
    if not feedback:
        return format_response(None, "Feedback not found", 404)
    return format_response(feedback, "Feedback fetched successfully", 200)


# ** Get Feedback by User ID and News ID
@feedback_bp.route("/user/<uuid:userID>/news/<uuid:newsID>", methods=["GET"])
def get_feedback_by_user_and_news(userID, newsID):
    feedback = get_feedback_by_userID_and_newsID(userID, newsID)
    if not feedback:
        return format_response(None, "Feedback not found", 404)
    return format_response(feedback, "Feedback fetched successfully", 200)


# ** Create Feedback
@feedback_bp.route("/", methods=["POST"])
def create_feedback():
    data = request.get_json()
    userID = data.get("userID")
    newsID = data.get("newsID")
    assessment = data.get("assessment")
    feedback = Feedback(userID=userID, newsID=newsID, assessment=assessment)

    insert_feedback(feedback)
    if feedback.id is None:
        return format_response(None, "Feedback creation failed", 400)
    return format_response(
        {
            "userID": feedback.userID,
            "newsID": feedback.newsID,
            "assessment": feedback.assessment,
        },
        "Feedback created successfully",
        201,
    )
