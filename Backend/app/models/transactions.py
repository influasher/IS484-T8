from sqlalchemy.dialects.postgresql import UUID
from app import db
from datetime import datetime
import uuid


class Transactions(db.Model):
    __tablename__ = 'transactions'

    txn_uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    client_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, index=True)
    datetime = db.Column(db.DateTime, nullable=False, index=True)
    source = db.Column(db.String(100), nullable=True)
    type = db.Column(db.Enum('Deposit', 'Withdrawal', 'Dividend', 'Buy', 'Sell', name='transactiontype'), nullable=False)
    currency = db.Column(db.Enum('USD', 'SGD', 'EUR', 'GBP', 'JPY', name='currency'), nullable=False)
    amount = db.Column(db.Numeric(precision=15, scale=2), nullable=False)
    desc = db.Column(db.Text, nullable=True)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entity.id'), nullable=True, index=True)
    quantity = db.Column(db.Double, nullable=True)
    price_per_share = db.Column(db.Double, nullable=True)

    client = db.relationship('User', backref='transactions')
    entity = db.relationship('Entity', backref='transactions')

    def __repr__(self):
        return f"<Transaction {self.txn_uuid} client={self.client_uuid} type={self.type} amount={self.amount}>"

    def to_dict(self):
        return {
            'txn_uuid': str(self.txn_uuid),
            'client_uuid': str(self.client_uuid),
            'datetime': self.datetime.isoformat() if self.datetime else None,
            'source': self.source,
            'type': self.type,
            'currency': self.currency,
            'amount': float(self.amount) if self.amount else None,
            'desc': self.desc,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'quantity': self.quantity,
            'price_per_share': self.price_per_share
        }