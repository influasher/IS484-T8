import uuid
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID
from app import db


class UserRole(Enum):
    CLIENT = "client"
    RELATIONSHIP_MANAGER = "relationship_manager"


class User(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    # password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    rm_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    clients = db.relationship(
        "User", backref=db.backref("relationship_manager", remote_side=[id])
    )

    def is_client(self):
        return self.role == UserRole.CLIENT

    def is_rm(self):
        return self.role == UserRole.RELATIONSHIP_MANAGER

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"
