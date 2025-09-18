from app.models.news import News
from sqlalchemy import any_, func, or_
from datetime import datetime, timedelta
from app import db
import time
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR


def news_by_ticker(ticker, page=1, per_page=3, sort_order="desc", filter_time="all"):
    """Get paginated, filtered, and sorted news by ticker"""

    query = News.query.filter(News.entities.any(ticker))

    # Apply time filtering
    if filter_time != "all":
        now = datetime.now()  # Ensure UTC consistency
        if filter_time == "24":
            query = query.filter(News.published_date >= now - timedelta(hours=24))
        elif filter_time == "48":
            query = query.filter(News.published_date >= now - timedelta(hours=48))
        elif filter_time == "7d":
            query = query.filter(News.published_date >= now - timedelta(days=7))

    # Apply sorting (asc = oldest first, desc = newest first)
    if sort_order == "asc":
        query = query.order_by(News.published_date.asc())
    else:
        query = query.order_by(News.published_date.desc())

    # Apply pagination
    news_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    if not news_paginated.items:
        return []

    news_list = [
        {
            "id": n.id,
            "publisher": n.publisher,
            "description": n.description,
            "summary": n.summary,
            "published_date": n.published_date.strftime("%Y-%m-%d %H:%M:%S"),
            "title": n.title,
            "url": n.url,
            "entities": n.entities,
            "score": n.score,
            "finbert_score": n.finbert_score,
            "second_model_score": n.second_model_score,
            "third_model_score": n.third_model_score,
            "sentiment": n.sentiment,
            "tags": n.tags,
            "confidence": n.confidence,
            "agreement_rate": n.agreement_rate,
            "company_names": n.company_names,
            "regions": n.regions,
            "sectors": n.sectors,
        }
        for n in news_paginated.items
    ]

    return {
        "news": news_list,
        "total": news_paginated.total,
        "pages": news_paginated.pages,
        "current_page": news_paginated.page,
        "next_page": news_paginated.next_num,
        "prev_page": news_paginated.prev_num,
        "per_page": per_page,
    }


def news_by_name(name, page=1, per_page=3, sort_order="desc", filter_time="all"):
    """Get paginated, filtered, and sorted news by company name"""

    query = News.query.filter(News.entities.contains(cast([name], ARRAY(VARCHAR))))

    # Apply time filtering
    if filter_time != "all":
        now = datetime.now()  # Ensure UTC consistency
        if filter_time == "24":
            query = query.filter(News.published_date >= now - timedelta(hours=24))
        elif filter_time == "48":
            query = query.filter(News.published_date >= now - timedelta(hours=48))
        elif filter_time == "7d":
            query = query.filter(News.published_date >= now - timedelta(days=7))

    # Apply sorting (asc = oldest first, desc = newest first)
    if sort_order == "asc":
        query = query.order_by(News.published_date.asc())
    else:
        query = query.order_by(News.published_date.desc())

    # Apply pagination
    news_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    if not news_paginated.items:
        return []

    news_list = [
        {
            "id": n.id,
            "publisher": n.publisher,
            "description": n.description,
            "summary": n.summary,
            "published_date": n.published_date.strftime("%Y-%m-%d %H:%M:%S"),
            "title": n.title,
            "url": n.url,
            "entities": n.entities,
            "score": n.score,
            "finbert_score": n.finbert_score,
            "second_model_score": n.second_model_score,
            "third_model_score": n.third_model_score,
            "sentiment": n.sentiment,
            "tags": n.tags,
            "confidence": n.confidence,
            "agreement_rate": n.agreement_rate,
            "company_names": n.company_names,
            "regions": n.regions,
            "sectors": n.sectors,
        }
        for n in news_paginated.items
    ]

    return {
        "news": news_list,
        "total": news_paginated.total,
        "pages": news_paginated.pages,
        "current_page": news_paginated.page,
        "next_page": news_paginated.next_num,
        "prev_page": news_paginated.prev_num,
        "per_page": per_page,
    }


def news_by_id(news_id):
    """Get news by ID"""
    news = News.query.get(news_id)
    if news:
        return {
            "id": news.id,
            "publisher": news.publisher,
            "description": news.description,
            "summary": news.summary,
            "published_date": news.published_date,
            "title": news.title,
            "url": news.url,
            "entities": news.entities,
            "score": news.score,
            "finbert_score": news.finbert_score,
            "second_model_score": news.second_model_score,
            "third_model_score": news.third_model_score,
            "sentiment": news.sentiment,
            "tags": news.tags,
            "confidence": news.confidence,
            "agreement_rate": news.agreement_rate,
            "company_names": news.company_names,
            "regions": news.regions,
            "sectors": news.sectors,
        }
    return None


def all_news(
    page=1, per_page=4, filter_time="all", sort_order="desc", search_term=None
):
    """Get all news"""
    # Query the news
    query = News.query

    # Apply search filter (if search_term exists)
    if search_term:
        query = query.filter(
            or_(
                News.title.ilike(f"%{search_term}%"),
                News.summary.ilike(f"%{search_term}%"),
                News.description.ilike(f"%{search_term}%"),
                search_term == any_(News.tags),
                search_term == any_(News.sectors),
                search_term == any_(News.regions),
                search_term == any_(News.company_names),
            )
        )

    # Filtering based on date
    if filter_time != "all":
        now = datetime.now()
        if filter_time == "24":
            query = query.filter(News.published_date >= now - timedelta(hours=24))
        elif filter_time == "48":
            query = query.filter(News.published_date >= now - timedelta(hours=48))
        elif filter_time == "7d":
            query = query.filter(News.published_date >= now - timedelta(days=7))

    # Sorting based on sentiment score
    if sort_order == "asc":
        query = query.order_by(News.published_date.asc())
    else:
        query = query.order_by(News.published_date.desc())

    news_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    news_list = []
    for n in news_paginated.items:
        news_list.append(
            {
                "id": n.id,
                "publisher": n.publisher,
                "description": n.description,
                "summary": n.summary,
                "published_date": n.published_date,
                "title": n.title,
                "url": n.url,
                "entities": n.entities,
                "score": n.score,
                "finbert_score": n.finbert_score,
                "second_model_score": n.second_model_score,
                "third_model_score": n.third_model_score,
                "sentiment": n.sentiment,
                "tags": n.tags,
                "confidence": n.confidence,
                "agreement_rate": n.agreement_rate,
                "company_names": n.company_names,
                "regions": n.regions,
                "sectors": n.sectors,
            }
        )

    return {
        "news": news_list,
        "total": news_paginated.total,
        "pages": news_paginated.pages,
        "current_page": news_paginated.page,
        "next_page": news_paginated.next_num,
        "prev_page": news_paginated.prev_num,
        "per_page": per_page,
    }


def resync_news_data():
    """
    Reprocess all news articles where sentiment data is missing.
    Commits after each update and tracks progress.
    """
    from app.utils.helpers import news_interpreter

    now = datetime.now()

    # Get all news articles where second_model_score is NULL
    news_to_update = News.query.filter(
        News.published_date >= now - timedelta(hours=48)
    ).all()

    if not news_to_update:
        return {"message": "No news articles to update."}

    total = len(news_to_update)
    updated = 0
    failed = 0

    for i, news in enumerate(news_to_update, start=1):
        try:
            time.sleep(10)  # Sleep to avoid rate limiting

            # Fetch the article details
            description = news.description or ""

            interpreted_news = news_interpreter(description, 100)

            metadata = interpreted_news.get("metadata", {})
            companies = metadata.get("companies", [])
            regions = metadata.get("regions", [])
            sectors = metadata.get("sectors", [])

            # update the news object with the new values
            news.company_names = companies
            news.regions = regions
            news.sectors = sectors

            db.session.commit()
            updated += 1

            print(f"[{i}/{total}] ✅ Updated news ID {news.id}")
        except Exception as e:
            db.session.rollback()
            failed += 1
            print(f"[{i}/{total}] ❌ Failed to update news ID {news.id} — {str(e)}")

    return {
        "message": "Resync complete.",
        "total": total,
        "updated": updated,
        "failed": failed,
    }
