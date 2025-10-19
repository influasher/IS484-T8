from flask import Blueprint, request, jsonify
from app import db
from app.models.client_portfolio import ClientPortfolio
from app.models.client_performance import ClientPerformance
from app.models.entity import Entity
from app.models.user import User
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/<client_id>', methods=['GET'])
def get_client_portfolio(client_id):
    """Get portfolio allocation for a specific client"""
    try:
        # Verify client exists
        client = User.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        # Get all portfolio holdings for this client
        portfolios = ClientPortfolio.query.filter_by(user_id=client_id).all()

        # Format allocation data
        allocation = []
        for portfolio in portfolios:
            entity = Entity.query.get(portfolio.entity_id)
            if entity:
                allocation.append({
                    'name': entity.ticker,
                    'value': portfolio.qty or 0,
                    'average_cost_basis': portfolio.average_cost_basis,
                    'total_invested': portfolio.total_invested,
                    'color': f'#{hash(entity.ticker) % 0xFFFFFF:06x}',  # Generate color from ticker
                    'market_value': portfolio.current_market_value,
                    'unrealized_pnl': portfolio.unrealized_pnl,
                    'unrealized_pnl_percent': portfolio.unrealized_pnl_percent,
                    'allocation_percent': portfolio.portfolio_allocation_percent
                })

        return jsonify({
            'client_id': client_id,
            'count': len(allocation),
            'allocation': allocation
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve portfolio', 'details': str(e)}), 500


@portfolio_bp.route('/performance/<client_id>', methods=['GET'])
def get_client_performance(client_id):
    """Get performance history for a specific client"""
    try:
        # Verify client exists
        client = User.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        # Get performance records for this client
        performances = ClientPerformance.query.filter_by(
            client_uuid=client_id
        ).order_by(ClientPerformance.datetime.asc()).all()

        # Format performance data
        performance_data = []
        for perf in performances:
            performance_data.append({
                'date': perf.datetime.isoformat() if perf.datetime else None,
                'value': perf.daily_performance
            })

        return jsonify({
            'client_id': client_id,
            'count': len(performance_data),
            'performance': performance_data
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve performance', 'details': str(e)}), 500
