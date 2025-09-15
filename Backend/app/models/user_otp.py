import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.postgresql import UUID
from app import db


class UserOTP(db.Model):
    __tablename__ = 'user_otp'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship
    user = db.relationship('User', backref='otps')

    def __init__(self, user_id, otp_code, expires_in_mins=1440):  # 1440 minutes = 1 day
        self.user_id = user_id
        self.otp_code = otp_code
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_mins)
        self.is_used = False

    def is_expired(self):
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now > expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()

    def mark_as_used(self):
        self.is_used = True
        db.session.commit()

    @classmethod
    def create_new_otp(cls, user_id, otp_code):
        """Create new OTP and deactivate all existing active OTPs for the user"""
        # Mark all existing active OTPs as used
        cls.query.filter_by(user_id=user_id, is_used=False).update({'is_used': True})
        db.session.flush()

        # Create new OTP
        new_otp = cls(user_id=user_id, otp_code=otp_code)
        db.session.add(new_otp)
        db.session.commit()
        return new_otp

    def __repr__(self):
        return f"<UserOTP {self.user_id} - {self.otp_code} - {'Used' if self.is_used else 'Active'}>"