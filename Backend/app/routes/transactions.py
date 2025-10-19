from flask import Blueprint, request, jsonify
from app import db
from app.models.transactions import Transactions
from app.models.user import User
from app.services.entities_service import get_id_by_entity
from app.services.data_ingestion_yfinance import get_stock_price
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid
from app.utils.decorators import jwt_required

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/add_transaction', methods=['POST'])
def add_transaction():
    print("add_transaction")
    """Add a new transaction"""
    try:
        data = request.json

        # Initialize variables
        txn_uuid = uuid.uuid4()
        client_uuid = data.get('client_uuid') or data.get('client_id')
        txn_datetime = datetime.fromisoformat(data['datetime']) if 'datetime' in data else datetime.now()
        txn_type = data['type']
        source = data.get('source', '')
        currency = data.get('currency', 'USD')
        amount = data.get('amount', 0)
        desc = data.get('desc', '')
        entity_id = None
        quantity = None
        price_per_share = None

        if txn_type in ["BUY", "SELL"]:
            print(f"calling get_id_by_entity({source})")
            entity_id = get_id_by_entity(source)
            print(entity_id)
            quantity = float(data.get('qty', 0))
            price_per_share = get_stock_price(source)
            currency = "USD"
            amount = price_per_share * quantity
            desc = f"{source} - {quantity} shares @ ${price_per_share:.2f}"

        # Create new transaction
        new_transaction = Transactions(
            txn_uuid=txn_uuid,
            client_uuid=client_uuid,
            datetime=txn_datetime,
            type=txn_type,
            source=source,
            currency=currency,
            amount=amount,
            desc=desc,
            entity_id=entity_id,
            quantity=quantity,
            price_per_share=price_per_share
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