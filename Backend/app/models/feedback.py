import uuid
from sqlalchemy.dialects.postgresql import UUID
from app import db


class Feedback(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userID = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    assessment = db.Column(
        db.String(50), nullable=False
    )  # e.g Bullish, Bearish, Neutral
    newsID = db.Column(UUID(as_uuid=True), db.ForeignKey("news.id"), nullable=False)

    def __repr__(self):
        return f"<Feedback {self.assessment}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "userID": str(self.userID),
            "assessment": self.assessment,
            "newsID": str(self.newsID),
        }
