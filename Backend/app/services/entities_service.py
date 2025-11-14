"""
Entity service module for managing entity data and sentiment calculations.
"""
from app.models import Entity
from sqlalchemy import or_, asc, desc, func
from app import db


def _get_entities_with_dynamic_sentiment(
    page=1, per_page=4, sort_order="name-asc", search_term=None,
    filter_operator=None, filter_value=None, time_period=7
):
    """Helper function to get entities with dynamically calculated sentiment for specified time period"""
    from app.services.entity_sentiment_aggregator import EntitySentimentAggregator

    # Get entities with basic filters first
    query = Entity.query

    # Apply search filter
    if search_term:
        query = query.filter(
            or_(
                Entity.name.ilike(f"%{search_term}%"),
                Entity.ticker.ilike(f"%{search_term}%"),
                Entity.summary.ilike(f"%{search_term}%"),
                Entity.classification.ilike(f"%{search_term}%"),
            )
        )

    # Get entities with tickers (needed for sentiment calculation)
    query = query.filter(Entity.ticker.isnot(None), Entity.ticker != '')

    # Get all entities first (will paginate after sentiment calculation)
    all_entities = query.all()

    if not all_entities:
        return []

    # Calculate dynamic sentiment for each entity
    aggregator = EntitySentimentAggregator(lookback_days=time_period)
    entities_with_sentiment = []

    for entity in all_entities:
        # Calculate sentiment for this time period
        articles = aggregator.entity_news_articles(entity.ticker)
        sentiment_result = aggregator.calculate_weighted_sentiment(articles)

        # Create entity data with dynamic sentiment
        entity_data = {
            "id": entity.id,
            "name": entity.name,
            "ticker": entity.ticker,
            "summary": entity.summary,
            # Use calculated sentiment instead of stored values
            "sentiment_score": sentiment_result['sentiment_score'],
            "finbert_score": sentiment_result['finbert_average'],
            "gemini_score": entity.gemini_score,  # Keep stored values for non-primary scores
            "open_ai_score": entity.open_ai_score,
            "confidence_score": sentiment_result['confidence_score'],
            "time_decay": sentiment_result['time_decay'],
            "simple_average": sentiment_result['simple_average'],
            "classification": sentiment_result['classification'],
            "asset_type": entity.asset_type,
            "sector": entity.sector,
            "sentiment_history": [],
        }
        entities_with_sentiment.append(entity_data)

    # Apply sentiment-based filtering if specified
    if filter_operator and filter_value:
        try:
            filter_val = float(filter_value)
            if filter_operator == ">":
                entities_with_sentiment = [e for e in entities_with_sentiment if e['sentiment_score'] and e['sentiment_score'] > filter_val]
            elif filter_operator == ">=":
                entities_with_sentiment = [e for e in entities_with_sentiment if e['sentiment_score'] and e['sentiment_score'] >= filter_val]
            elif filter_operator == "=":
                entities_with_sentiment = [e for e in entities_with_sentiment if e['sentiment_score'] and e['sentiment_score'] == filter_val]
            elif filter_operator == "<=":
                entities_with_sentiment = [e for e in entities_with_sentiment if e['sentiment_score'] and e['sentiment_score'] <= filter_val]
            elif filter_operator == "<":
                entities_with_sentiment = [e for e in entities_with_sentiment if e['sentiment_score'] and e['sentiment_score'] < filter_val]
        except (ValueError, TypeError):
            pass  # Skip filtering if value can't be converted

    # Apply sentiment-based sorting
    if sort_order == "sentiment-high":
        entities_with_sentiment.sort(key=lambda x: x['sentiment_score'] or 0, reverse=True)
    elif sort_order == "sentiment-low":
        entities_with_sentiment.sort(key=lambda x: x['sentiment_score'] or 0)
    elif sort_order == "name-asc":
        entities_with_sentiment.sort(key=lambda x: x['name'].lower())
    elif sort_order == "name-desc":
        entities_with_sentiment.sort(key=lambda x: x['name'].lower(), reverse=True)

    # Apply pagination
    total = len(entities_with_sentiment)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_entities = entities_with_sentiment[start_idx:end_idx]

    return {
        "entities": paginated_entities,
        "total": total,
        "pages": total_pages,
        "current_page": page,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None,
        "per_page": per_page,
    }


def get_ticker_by_entity(entity_name):
    """Get ticker by entity name"""
    entity = Entity.query.filter(Entity.name == entity_name).first()
    if entity:
        return entity.ticker
    return None


def get_id_by_entity(ticker_or_name):
    """Get entity ID by ticker or name"""
    # First try to find by ticker
    entity = Entity.query.filter(Entity.ticker == ticker_or_name).first()

    # If not found, try to find by name
    if not entity:
        entity = Entity.query.filter(Entity.name == ticker_or_name).first()

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


def get_all_entities(page=1, per_page=4, sort_order="name-asc", search_term=None, filter_operator=None, filter_value=None, time_period=None):
    """Get paginated and sorted entities by ticker with optional dynamic sentiment calculation"""

    # If time_period is specified and not 7 (baseline), calculate dynamic sentiment
    if time_period is not None and time_period != 7:
        return _get_entities_with_dynamic_sentiment(page, per_page, sort_order, search_term, filter_operator, filter_value, time_period)

    # Otherwise use stored sentiment values (baseline 7-day or regular query)
    query = Entity.query

    # Apply search filter (if search_term exists)
    if search_term:
        query = query.filter(
            or_(
                Entity.name.ilike(f"%{search_term}%"),
                Entity.ticker.ilike(f"%{search_term}%"),
                Entity.summary.ilike(f"%{search_term}%"),
                Entity.classification.ilike(f"%{search_term}%"),
            )
        )

    # Apply advanced filter (if filter_operator and filter_value exist)
    if filter_operator and filter_value:
        try:
            filter_val = float(filter_value)
            if filter_operator == ">":
                query = query.filter(Entity.sentiment_score > filter_val)
            elif filter_operator == ">=":
                query = query.filter(Entity.sentiment_score >= filter_val)
            elif filter_operator == "=":
                query = query.filter(Entity.sentiment_score == filter_val)
            elif filter_operator == "<=":
                query = query.filter(Entity.sentiment_score <= filter_val)
            elif filter_operator == "<":
                query = query.filter(Entity.sentiment_score < filter_val)
        except (ValueError, TypeError):
            # If filter_value cannot be converted to float, skip filtering
            pass

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

    entities_list = [
        {
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
            "sentiment_history": [],
        }
        for entity in entities_paginated.items
    ]

    return {
        "entities": entities_list,
        "total": entities_paginated.total,
        "pages": entities_paginated.pages,
        "current_page": entities_paginated.page,
        "next_page": entities_paginated.next_num,
        "prev_page": entities_paginated.prev_num,
        "per_page": per_page,
    }


# update entity sentiment
def update_entity_sentiment(
    ticker,
    sentiment_score,
    confidence_score,
    time_decay_score,
    simple_average_score,
    classification,
):
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
        return {
            "avg_score": entity.sentiment_score,
            "simple_average": entity.simple_average,
            "time_decay": entity.time_decay,
            "confidence_score": entity.confidence_score,
            "classification": entity.classification,
            "ticker": entity.ticker,
            "name": entity.name,
        }
    return None
