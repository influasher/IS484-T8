import uuid
from sqlalchemy.dialects.postgresql import UUID
from app import db
from datetime import datetime


class ClientPortfolio(db.Model):
    __tablename__ = 'client_portfolio'

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), primary_key=True, nullable=False)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entity.id'), primary_key=True, nullable=False)
    qty = db.Column(db.Integer, nullable=True)
    average_cost_basis = db.Column(db.Double, nullable=True)
    total_invested = db.Column(db.Double, nullable=True)
    first_purchase_date = db.Column(db.DateTime, nullable=True)
    last_transaction_date = db.Column(db.DateTime, nullable=True)
    current_price = db.Column(db.Double, nullable=True)
    current_market_value = db.Column(db.Double, nullable=True)
    unrealized_pnl = db.Column(db.Double, nullable=True)
    unrealized_pnl_percent = db.Column(db.Double, nullable=True)
    portfolio_allocation_percent = db.Column(db.Double, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='portfolio')
    entity = db.relationship('Entity', backref='portfolios')

    def __repr__(self):
        return f"<ClientPortfolio user_id={self.user_id} entity_id={self.entity_id}>"

    def to_dict(self):
        return {
            'user_id': str(self.user_id),
            'entity_id': str(self.entity_id),
            'qty': self.qty,
            'average_cost_basis': self.average_cost_basis,
            'total_invested': self.total_invested,
            'first_purchase_date': self.first_purchase_date.isoformat() if self.first_purchase_date else None,
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'current_price': self.current_price,
            'current_market_value': self.current_market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percent': self.unrealized_pnl_percent,
            'portfolio_allocation_percent': self.portfolio_allocation_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }