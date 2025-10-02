import uuid
from sqlalchemy.dialects.postgresql import UUID
from app import db
from datetime import datetime, timezone


class ClientPortfolio(db.Model):
    __tablename__ = 'client_portfolio'

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), primary_key=True, nullable=False)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entity.id'), primary_key=True, nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    # Calculated fields derived from transactions
    average_cost_basis = db.Column(db.Float, nullable=True)
    total_invested = db.Column(db.Float, nullable=True)
    first_purchase_date = db.Column(db.DateTime, nullable=True)
    last_transaction_date = db.Column(db.DateTime, nullable=True)

    # Current market data (updated periodically)
    current_price = db.Column(db.Float, nullable=True)
    current_market_value = db.Column(db.Float, nullable=True)
    unrealized_pnl = db.Column(db.Float, nullable=True)
    unrealized_pnl_percent = db.Column(db.Float, nullable=True)

    # Portfolio allocation
    portfolio_allocation_percent = db.Column(db.Float, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

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
            'current_price': self.current_price,
            'current_market_value': self.current_market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percent': self.unrealized_pnl_percent,
            'portfolio_allocation_percent': self.portfolio_allocation_percent,
            'first_purchase_date': self.first_purchase_date.isoformat() if self.first_purchase_date else None,
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_current_values(self):
        """Update current market values and P&L"""
        if self.current_price and self.qty:
            self.current_market_value = self.qty * self.current_price

            if self.total_invested and self.total_invested > 0:
                self.unrealized_pnl = self.current_market_value - self.total_invested
                self.unrealized_pnl_percent = (self.unrealized_pnl / self.total_invested) * 100

    def get_holding_period_days(self):
        """Get days since first purchase"""
        if self.first_purchase_date:
            return (datetime.now(timezone.utc) - self.first_purchase_date).days
        return 0

    def is_long_term_holding(self):
        """Check if position qualifies for long-term capital gains (>365 days)"""
        return self.get_holding_period_days() > 365

    def calculate_portfolio_allocation(self, total_portfolio_value):
        """Calculate what percentage of total portfolio this position represents"""
        if self.current_market_value and total_portfolio_value > 0:
            self.portfolio_allocation_percent = (self.current_market_value / total_portfolio_value) * 100
            return self.portfolio_allocation_percent
        return 0.0