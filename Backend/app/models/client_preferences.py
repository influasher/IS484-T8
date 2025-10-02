import uuid
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app import db
from datetime import datetime, timezone


class ClientPreferences(db.Model):
    __tablename__ = 'client_preferences'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, unique=True)
    holding = db.Column(db.Float, nullable=True)
    overall_pl = db.Column(db.Float, nullable=True)
    stop_loss_tolerance = db.Column(db.Float, nullable=True)
    risk_cap = db.Column(db.String, nullable=True)
    sectors = db.Column(ARRAY(db.String), nullable=True)

    max_single_position_percent = db.Column(db.Float, nullable=True, default=15.0)
    max_sector_allocation_percent = db.Column(db.Float, nullable=True, default=40.0)
    min_cash_reserve_percent = db.Column(db.Float, nullable=True, default=10.0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

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
            'max_single_position_percent': self.max_single_position_percent,
            'max_sector_allocation_percent': self.max_sector_allocation_percent,
            'min_cash_reserve_percent': self.min_cash_reserve_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_risk_profile_defaults(self):
        """Returns risk management defaults based on risk_cap"""
        profiles = {
            'Conservative': {
                'max_single_position_percent': 10.0,
                'max_sector_allocation_percent': 30.0,
                'min_cash_reserve_percent': 15.0
            },
            'Moderate': {
                'max_single_position_percent': 15.0,
                'max_sector_allocation_percent': 40.0,
                'min_cash_reserve_percent': 10.0
            },
            'Aggressive': {
                'max_single_position_percent': 20.0,
                'max_sector_allocation_percent': 50.0,
                'min_cash_reserve_percent': 5.0
            }
        }
        return profiles.get(self.risk_cap, profiles['Moderate'])

    def apply_risk_profile_defaults(self):
        """Apply default risk settings based on risk_cap if not already set"""
        if not any([self.max_single_position_percent, self.max_sector_allocation_percent, self.min_cash_reserve_percent]):
            defaults = self.get_risk_profile_defaults()
            self.max_single_position_percent = defaults['max_single_position_percent']
            self.max_sector_allocation_percent = defaults['max_sector_allocation_percent']
            self.min_cash_reserve_percent = defaults['min_cash_reserve_percent']