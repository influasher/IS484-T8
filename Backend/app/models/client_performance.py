from sqlalchemy.dialects.postgresql import UUID
from app import db
from datetime import datetime


class ClientPerformance(db.Model):
    __tablename__ = 'client_performance'

    client_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), primary_key=True, nullable=False)
    datetime = db.Column(db.DateTime, primary_key=True, nullable=False)
    daily_performance = db.Column(db.Double, nullable=True)

    client = db.relationship('User', backref='performance_records')

    def __repr__(self):
        return f"<ClientPerformance client={self.client_uuid} datetime={self.datetime}>"

    def to_dict(self):
        return {
            'client_uuid': str(self.client_uuid),
            'datetime': self.datetime.isoformat() if self.datetime else None,
            'daily_performance': self.daily_performance
        }