import uuid
from sqlalchemy.dialects.postgresql import UUID
from app import db

class Entity(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False, unique=True)
    ticker = db.Column(db.String(20), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    sentiment_score = db.Column(db.Float, nullable=True)
    finbert_score = db.Column(db.Float, nullable=True)
    gemini_score = db.Column(db.Float, nullable=True)
    open_ai_score = db.Column(db.Float, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    time_decay = db.Column(db.Float, nullable=True)
    simple_average = db.Column(db.Float, nullable=True)
    classification = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Entity {self.name}>"
