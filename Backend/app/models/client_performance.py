from sqlalchemy.dialects.postgresql import UUID
from app import db
from datetime import datetime


class ClientPerformance(db.Model):
    __tablename__ = 'client_performance'

    client_uuid = db.Column(UUID(as_uuid=True), primary_key=True, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.DateTime, primary_key=True, nullable=False, default=datetime.utcnow)
    daily_performance = db.Column(db.Float, nullable=False)

    client = db.relationship('User', backref='performance_records')

    def __repr__(self):
        return f"<Performance client={self.client_uuid} datetime={self.datetime}>"

    def to_dict(self):
        return {
            'client_uuid': str(self.client_uuid),
            'datetime': self.datetime.isoformat(),
            'daily_performance': self.daily_performance
        }