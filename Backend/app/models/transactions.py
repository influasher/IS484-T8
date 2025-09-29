from sqlalchemy.dialects.postgresql import UUID
from app import db
from datetime import datetime
import uuid


class Transactions(db.Model):
    __tablename__ = 'transactions'

    txn_uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    client_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, index=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(precision=15, scale=2), nullable=False)
    desc = db.Column(db.Text, nullable=True)

    client = db.relationship('User', backref='transactions')

    def __repr__(self):
        return f"<Transactions {self.txn_uuid} client={self.client_uuid} amount={self.amount}>"

    def to_dict(self):
        return {
            'txn_uuid': str(self.txn_uuid),
            'client_uuid': str(self.client_uuid),
            'datetime': self.datetime.isoformat(),
            'source': self.source,
            'type': self.type,
            'currency': self.currency,
            'amount': float(self.amount),
            'desc': self.desc
        }