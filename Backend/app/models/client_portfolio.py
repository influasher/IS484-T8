import uuid
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app import db


class ClientPortfolio(db.Model):
    __tablename__ = 'client_portfolio'

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, db.ForeignKey('user.id'), nullable=False)
    entity_name = db.Column(UUID(as_uuid=True), primary_key=True, db.ForeignKey('entity.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref='portfolio')
    entity = db.relationship('Entity', backref='portfolios')

    def __repr__(self):
        return f"<ClientPortfolio user_id={self.user_id} entity={self.entity_name}>"

    def to_dict(self):
        return {
            'user_id': str(self.user_id),
            'entity_name': str(self.entity_name),
            'qty': self.qty
        }