import uuid
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app import db


class ClientPreferences(db.Model):
    __tablename__ = 'client_preferences'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, unique=True)
    holding = db.Column(db.Float, nullable=True)
    overall_pl = db.Column(db.Float, nullable=True)
    stop_loss_tolerance = db.Column(db.Boolean, default=False, nullable=False)
    risk_cap = db.Column(db.Float, nullable=True)
    sectors = db.Column(ARRAY(db.String), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', backref='preferences')

    def __repr__(self):
        return f"<ClientPreferences {self.user_id}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'holding': self.holding,
            'overall_pl': self.overall_pl,
            'stop_loss_tolerance': self.stop_loss_tolerance,
            'risk_cap': self.risk_cap,
            'sectors': self.sectors,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }