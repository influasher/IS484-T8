from flask import Blueprint, request, jsonify
from app import db
from app.models.transactions import Transactions
from app.models.user import User
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/', methods=['POST'])
def add_transaction():
    """Add a new transaction"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['client_uuid', 'datetime', 'type', 'currency', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new transaction
        new_transaction = Transactions(
            txn_uuid=uuid.uuid4(),
            client_uuid=data['client_uuid'],
            datetime=datetime.fromisoformat(data['datetime']),
            source=data.get('source'),
            type=data['type'],
            currency=data['currency'],
            amount=data['amount'],
            desc=data.get('desc'),
            entity_id=data.get('entity_id'),
            quantity=data.get('quantity'),
            price_per_share=data.get('price_per_share')
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Transaction created successfully',
            'transaction': new_transaction.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error', 'details': str(e)}), 400
    except ValueError as e:
        return jsonify({'error': 'Invalid data format', 'details': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create transaction', 'details': str(e)}), 500


@transactions_bp.route('/', methods=['GET'])
def get_all_transactions():
    print("entered get transactions")
    """Retrieve all transactions"""
    try:
        transactions = Transactions.query.all()
        return jsonify({
            'count': len(transactions),
            'transactions': [txn.to_dict() for txn in transactions]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve transactions', 'details': str(e)}), 500


@transactions_bp.route('/client', methods=['GET'])
def get_transactions_by_client():
    """Retrieve all transactions for a specific client"""
    try:
        client_id = request.json.get('client_id')
        
        if not client_id:
            return jsonify({'error': 'Missing client_id in request body'}), 400
        
        # Verify client exists
        client = User.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Get all transactions for this client
        transactions = Transactions.query.filter_by(client_uuid=client_id).all()
        
        return jsonify({
            'client_id': client_id,
            'count': len(transactions),
            'transactions': [txn.to_dict() for txn in transactions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve transactions', 'details': str(e)}), 500


# Alternative route using query parameters instead of request body
@transactions_bp.route('/client/<client_id>', methods=['GET'])
def get_transactions_by_client_param(client_id):
    """Retrieve all transactions for a specific client using URL parameter"""
    try:
        # Verify client exists
        client = User.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Get all transactions for this client
        transactions = Transactions.query.filter_by(client_uuid=client_id).all()
        
        return jsonify({
            'client_id': client_id,
            'count': len(transactions),
            'transactions': [txn.to_dict() for txn in transactions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve transactions', 'details': str(e)}), 500