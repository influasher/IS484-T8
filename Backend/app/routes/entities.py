from flask import Blueprint, request
from app.models.entity import Entity
from app.services.data_ingestion_finviz import get_stock_fundamentals
from app.services.data_ingestion_yfinance import get_stock_price, get_stock_history
from app.services.sentiment_history_services import get_sentiment_history_by_entity_id, create_sentiment_history
from app.services.entities_service import get_all_entities, get_all_ticker_entities
from app import db
from app.utils.decorators import jwt_required
from app.utils.helpers import format_response

entities_bp = Blueprint('entities', __name__)

# Helper function to convert frontend period to yfinance period
def convert_period_to_yfinance(period):
    """Convert frontend period format to yfinance compatible format"""
    period_mapping = {
        '1D': '1d',
        '1W': '5d',     # yfinance doesn't have 1w, use 5d for 1 week
        '1M': '1mo',
        '3M': '3mo', 
        '6M': '6mo',
        '1Y': '1y',
        'YTD': 'ytd',
        '5Y': '5y'
    }
    return period_mapping.get(period, '1y')  # default to 1 year

# ** Get Entities
@entities_bp.route("/", methods=['GET'])
def get_entities():
    """Get paginated entities"""
    page = request.args.get('page', 1, type=int)  # Get the 'page' parameter from the request, default is 1
    per_page = request.args.get('per_page', 4, type=int)  # Get 'per_page' parameter, default is 10

    search_term = request.args.get('search', None)  # Get search term
    sort_order = request.args.get('sort_order', 'name-asc')  # Get sorting params - Default to ascending

    entities_list = get_all_entities(page, per_page, sort_order, search_term)

    if not entities_list:
        return format_response([], "Entities not found", 404)
    return format_response(entities_list, "Entities fetched successfully", 200)

@entities_bp.route('/get_all_tickers', methods=['GET'])
def get_all_tickers():
    tickers = get_all_ticker_entities()
    if not tickers:
        return format_response([], "Tickers not found", 404)
    return format_response(tickers, "Tickers fetched successfully", 200)

# ** Create Entity
@entities_bp.route('/', methods=['POST'])
@jwt_required
def create_entity():
    data = request.get_json()
    name = data.get('name')
    ticker = data.get('ticker')
    entity = Entity(name=name, ticker=ticker)

    db.session.add(entity)
    db.session.commit()
    return format_response({
        "name": entity.name,
        "ticker": entity.ticker,
        "summary": entity.summary,
    }, "Entity created successfully", 201)

# ** Update Entity
@entities_bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required
def update_entity(id):
    entity = Entity.query.get(id)
    if entity is None:
        return format_response(None, "Entity not found", 404)

    data = request.get_json()
    entity.sentiment_score = data.get('sentiment_score')
    entity.finbert_score = data.get('finbert_score')
    entity.gemini_score = data.get('gemini_score')
    entity.open_ai_score = data.get('open_ai_score')
    entity.confidence_score = data.get('confidence_score')
    entity.time_decay = data.get('time_decay')
    entity.simple_average = data.get('simple_average')
    entity.classification = data.get('classification')

    db.session.commit()
    return format_response({
        "id": entity.id,
        "sentiment_score": entity.sentiment_score,
        "finbert_score": entity.finbert_score,
        "gemini_score": entity.gemini_score,
        "open_ai_score": entity.open_ai_score,
        "confidence_score": entity.confidence_score,
        "time_decay": entity.time_decay,
        "simple_average": entity.simple_average,
        "classification": entity.classification
    }, "Entity updated successfully", 200)

# ** Get Entity Details
@entities_bp.route('/<string:ticker>', methods=['GET'])
def get_entity_details(ticker):
    entity = Entity.query.filter_by(ticker=ticker).first()
    if entity is None:
        return format_response(None, "Entity not found", 404)
    return format_response({
        "id": entity.id,
        "name": entity.name,
        "ticker": entity.ticker,
        "summary": entity.summary,
        "sentiment_score": entity.sentiment_score,
        "finbert_score": entity.finbert_score,
        "gemini_score": entity.gemini_score,
        "open_ai_score": entity.open_ai_score,
        "confidence_score": entity.confidence_score,
        "time_decay": entity.time_decay,
        "simple_average": entity.simple_average,
        "classification": entity.classification
    }, "Entity fetched successfully", 200)

# ** get entity stock price
@entities_bp.route('/<uuid:id>/stock', methods=['GET'])
def get_entity_stock_price(id):
    entity = Entity.query.get(id)
    if entity is None:
        return format_response(None, "Entity not found", 404)
 
    # call the stock price service
    stock_price = get_stock_price(entity.ticker)

    return format_response({
        "name": entity.name,
        "stock_price": stock_price,
    }, "Stock price fetched successfully", 200)

# ** get stock chart data with period support
@entities_bp.route('/<uuid:id>/chart', methods=['GET'])
def get_entity_stock_chart(id):
    print("Fetching stock chart for entity ID:", id)
    
    # Get period from query parameters
    period = request.args.get('period', '1Y')  # Default to 1 year
    print(f"Period requested: {period}")
    
    entity = Entity.query.get(id)
    if entity is None:
        return format_response(None, "Entity not found", 404)
    
    # Convert frontend period to yfinance format
    yf_period = convert_period_to_yfinance(period)
    
    # call the stock price service with period
    # You'll need to modify your get_stock_history function to accept period parameter
    # For now, this assumes your function can handle the period parameter
    try:
        stock_chart = get_stock_history(entity.ticker, period=yf_period)
    except TypeError:
        # Fallback if your current function doesn't support period parameter yet
        stock_chart = get_stock_history(entity.ticker)

    return format_response({
        "name": entity.name,
        "ticker": entity.ticker,
        "period": period,
        "stock_chart": stock_chart,
    }, f"Stock chart fetched successfully for {period}", 200)

# ** get IRX chart data with period support
@entities_bp.route('/ticker=^IRX/chart', methods=['GET'])
def get_irx_chart():
    print("Fetching IRX chart data")
    
    # Get period from query parameters
    period = request.args.get('period', '1Y')  # Default to 1 year
    print(f"IRX period requested: {period}")
    
    # Convert frontend period to yfinance format
    yf_period = convert_period_to_yfinance(period)
    
    # call the stock price service for IRX with period
    try:
        stock_chart = get_stock_history("^IRX", period=yf_period)
    except TypeError:
        # Fallback if your current function doesn't support period parameter yet
        stock_chart = get_stock_history("^IRX")

    return format_response({
        "ticker": "^IRX",
        "name": "13 Week Treasury Bill",
        "period": period,
        "stock_chart": stock_chart,
    }, f"IRX chart fetched successfully for {period}", 200)

@entities_bp.route('/<string:ticker>/fundamental', methods=['GET'])
def get_entity_fundamental(ticker):
    stock_fundamentals = get_stock_fundamentals(ticker)
    return format_response({
        "ticker": ticker,
        "fundamentals":stock_fundamentals}, 
        "Stock fundamentals fetched successfully", 200)