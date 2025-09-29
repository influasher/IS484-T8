from app.models import Feedback
from app import db


def get_feedback_by_userID(userID):
    feedback_list = Feedback.query.filter(Feedback.userID == userID).all()
    return [feedback.to_dict() for feedback in feedback_list]


def get_feedback_by_newsID(newsID):
    feedback_list = Feedback.query.filter(Feedback.newsID == newsID).all()
    return [feedback.to_dict() for feedback in feedback_list]


def get_feedback_by_userID_and_newsID(userID, newsID):
    feedback = Feedback.query.filter(
        Feedback.userID == userID, Feedback.newsID == newsID
    ).first()
    return feedback.to_dict() if feedback else None


def insert_feedback(feedback):
    db.session.add(feedback)
    db.session.commit()
