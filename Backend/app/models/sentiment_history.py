import uuid
from sqlalchemy.dialects.postgresql import UUID
from app import db

class SentimentHistory(db.Model):    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entity.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    sentiment_score = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<SentimentHistory {self.entity_id} - {self.date} - {self.sentiment_score}>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'entity_id': str(self.entity_id),
            'date': self.date.strftime('%Y-%m-%d'),
            'sentiment_score': self.sentiment_score
        }