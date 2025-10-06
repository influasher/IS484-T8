from sqlalchemy.dialects.postgresql import UUID
from app import db
from datetime import datetime, timezone
from enum import Enum
import uuid


class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    DIVIDEND = "DIVIDEND"
    BUY = "BUY"
    SELL = "SELL"


class Currency(Enum):
    USD = "USD"
    SGD = "SGD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


class Transactions(db.Model):
    __tablename__ = 'transactions'

    txn_uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    client_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, index=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    source = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    currency = db.Column(db.Enum(Currency), nullable=False)
    amount = db.Column(db.Numeric(precision=15, scale=2), nullable=False)
    desc = db.Column(db.Text, nullable=True)

    # Stock-specific fields (for Buy/Sell transactions)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entity.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    price_per_share = db.Column(db.Float, nullable=True)

    client = db.relationship('User', backref='transactions')
    entity = db.relationship('Entity', backref='stock_transactions')

    def __repr__(self):
        return f"<Transactions {self.txn_uuid} client={self.client_uuid} amount={self.amount}>"

    def to_dict(self):
        return {
            'txn_uuid': str(self.txn_uuid),
            'client_uuid': str(self.client_uuid),
            'datetime': self.datetime.isoformat(),
            'source': self.source,
            'type': self.type.value if self.type else None,
            'currency': self.currency.value if self.currency else None,
            'amount': float(self.amount),
            'desc': self.desc,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'quantity': self.quantity,
            'price_per_share': self.price_per_share
        }

    def is_stock_transaction(self):
        """Check if this is a stock buy/sell transaction"""
        return self.type in [TransactionType.BUY, TransactionType.SELL]

    def get_total_value(self):
        """Get total transaction value (for stock transactions: quantity × price)"""
        if self.is_stock_transaction() and self.quantity and self.price_per_share:
            return float(self.quantity * self.price_per_share)
        return float(self.amount)
