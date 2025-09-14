from app.models import Entity
from sqlalchemy import any_, or_, asc, desc, func
from app import db

def get_ticker_by_entity(entity_name):
    """Get ticker by entity name"""
    entity = Entity.query.filter(Entity.name == entity_name).first()
    if entity:
        return entity.ticker
    return None

def get_id_by_entity(entity_name):
    """Get ticker by entity name"""
    entity = Entity.query.filter(Entity.name == entity_name).first()
    if entity:
        return entity.id
    return None

def get_all_ticker_entities():
    """Get all entities with tickers"""
    ticker_list = []
    entities = Entity.query.all()
    if not entities:
        return []
    for entity in entities:
        ticker_list.append({"ticker": entity.ticker, "name": entity.name})

    return ticker_list

def get_all_entities(page=1, per_page=4, sort_order="name-asc", search_term=None):
    """Get paginated and sorted entities by ticker"""

    query = Entity.query

    # Apply search filter (if search_term exists)
    if search_term:
        query = query.filter(
            or_(
            Entity.name.ilike(f"%{search_term}%"),
            Entity.ticker.ilike(f"%{search_term}%"),
            Entity.summary.ilike(f"%{search_term}%"),
            Entity.classification.ilike(f"%{search_term}%")
            )
        )
        
    # Apply sorting

    if sort_order == "name-asc":
        query = query.order_by(func.lower(Entity.name).asc())
    elif sort_order == "name-desc":
        query = query.order_by(func.lower(Entity.name).desc())
    elif sort_order == "sentiment-high":
        query = query.order_by(desc(Entity.sentiment_score))
    elif sort_order == "sentiment-low":
        query = query.order_by(asc(Entity.sentiment_score))
    else:
        query = query.order_by(desc(Entity.id))  # default sort

    # Apply pagination
    entities_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    if not entities_paginated.items:
        return []

    entities_list = [{
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
            "classification": entity.classification,
            "sentiment_history": []
    } for entity in entities_paginated.items]

    return {
        "entities": entities_list,
        "total": entities_paginated.total,
        "pages": entities_paginated.pages,
        "current_page": entities_paginated.page,
        "next_page": entities_paginated.next_num,
        "prev_page": entities_paginated.prev_num,
        "per_page": per_page
    }

# update entity sentiment
def update_entity_sentiment(ticker, sentiment_score, confidence_score, time_decay_score, simple_average_score, classification):
    """Update entity sentiment"""
    entity = Entity.query.filter(Entity.ticker == ticker).first()
    if entity:
        entity.sentiment_score = sentiment_score
        entity.confidence_score = confidence_score
        entity.time_decay = time_decay_score
        entity.simple_average = simple_average_score
        entity.classification = classification
        db.session.commit()
        return True
    return False

def get_entity_details(ticker):
    """Get entity details by ticker"""
    entity = Entity.query.filter(Entity.ticker == ticker).first()
    if entity:
        return {'avg_score' : entity.sentiment_score, 
                'simple_average' : entity.simple_average, 
                'time_decay' : entity.time_decay, 
                'confidence_score' : entity.confidence_score, 
                'classification' : entity.classification,
                'ticker' : entity.ticker,
                'name' : entity.name}
    return None