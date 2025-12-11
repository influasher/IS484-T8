from flask import Blueprint, request
import time
from app.services.news_services import (
    news_by_ticker,
    news_by_id,
    all_news,
    resync_news_data,
)
from app.services.data_ingestion_finviz import get_finviz_news_by_ticker, get_all_finviz
from app.services.data_ingestion_gnews import (
    get_gnews_news_by_ticker,
    get_all_top_gnews, get_premium_news_sources,
)
from app.services.data_ingestion_yfinance import get_stock_news
from app.services.entities_service import get_all_ticker_entities
from app.utils.helpers import format_response, format_date_into_tuple_for_gnews
from datetime import date, timedelta

news_bp = Blueprint("news", __name__)


def check_scraping_dependencies():
    """
    Check if heavy scraping dependencies are installed.

    Returns None if dependencies are available, otherwise returns a Flask response
    with 503 Service Unavailable and installation instructions.

    This allows scraping endpoints to work in development (with jobs/ deps installed)
    while gracefully failing in production (without heavy deps).
    """
    try:
        from app.services.article_scraper import _ensure_deps_loaded
        _ensure_deps_loaded()  # Will raise ImportError if crawl4ai missing
        return None  # Dependencies available
    except ImportError as e:
        return format_response(
            {
                "error": "Heavy dependencies not installed",
                "install_command": "cd Backend && uv pip install -e jobs/",
                "note": "This endpoint is for local testing only. Use news-processor CronJob for production."
            },
            f"Scraping dependencies missing: {str(e)}",
            503  # Service Unavailable
        )


@news_bp.route("/gnews/premium", methods=["POST"])
def ingest_premium_news_gnews_entity():
    """
    Test endpoint for news scraping (DEVELOPMENT ONLY).

    Requires heavy dependencies (crawl4ai, spacy, torch).
    To enable locally: cd Backend && uv pip install -e jobs/

    In production, this endpoint returns 503 as heavy deps are not installed.
    Use the news-processor CronJob for production scraping.
    """
    # Check if scraping dependencies are available
    dep_check = check_scraping_dependencies()
    if dep_check:
        return dep_check

    ticker = request.json.get("entity")

    # Get the start_date from 24hr before today and end_date as today
    start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = date.today().strftime("%Y-%m-%d")

    # Format the date into a tuple for gnews
    format_start_date = format_date_into_tuple_for_gnews(start_date)
    format_end_date = format_date_into_tuple_for_gnews(end_date)

    # Get the news using gnews and save it to the database
    news = get_premium_news_sources(ticker, format_start_date, format_end_date)

    if len(news) > 0:
        return format_response(
            news, "News data generated and saved successfully", 201
        )

    return format_response([], "No news data found", 404)


# ** generate news data based on ticker
@news_bp.route("/gnews", methods=["POST"])
def ingest_news_gnews_entity():
    """Test endpoint for GNews scraping. Requires: uv pip install -e jobs/"""
    # Check dependencies
    dep_check = check_scraping_dependencies()
    if dep_check:
        return dep_check

    # Get the entity, period, start_date, and end_date from the request
    ticker = request.json.get("entity")

    # Get the ticker from the entity
    # ticker = get_ticker_by_entity(entity)
    # print(ticker)

    # Get the start_date from 24hr before today and end_date as today
    start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = date.today().strftime("%Y-%m-%d")

    # Format the date into a tuple for gnews
    format_start_date = format_date_into_tuple_for_gnews(start_date)
    format_end_date = format_date_into_tuple_for_gnews(end_date)

    # Get the news using gnews and save it to the database
    news = get_gnews_news_by_ticker(ticker, format_start_date, format_end_date)

    if len(news) > 0:
        return format_response(
            news, "News data generated and saved successfully", 201
        )

    return format_response([], "No news data found", 404)


# ** generate news data based on ticker using finviz
@news_bp.route("/finviz", methods=["POST"])
def ingest_news_finviz_entity():
    """Test endpoint for Finviz scraping. Requires: uv pip install -e jobs/"""
    # Check dependencies
    dep_check = check_scraping_dependencies()
    if dep_check:
        return dep_check

    # Get the entity, period, start_date, and end_date from the request
    ticker = request.json.get("entity")

    # Get the ticker from the entity
    # ticker = get_ticker_by_entity(entity)

    # Get the news using finviz and save it to the database
    news = get_finviz_news_by_ticker(ticker)

    if len(news) > 0:
        return format_response(news, "News data generated and saved successfully", 201)

    return format_response([], "No news data found", 404)


# ** generate news data based on ticker using yfinance
@news_bp.route("/yfinance", methods=["POST"])
def ingest_news_yfinance_entity():
    """Test endpoint for yfinance scraping. Requires: uv pip install -e jobs/"""
    # Check dependencies
    dep_check = check_scraping_dependencies()
    if dep_check:
        return dep_check

    # Get the entity, period, start_date, and end_date from the request
    ticker = request.json.get("entity")

    # Get the ticker from the entity
    # ticker = get_ticker_by_entity(name)

    # Get the news using yfinance and save it to the database
    news = get_stock_news(ticker)

    if len(news) > 0:
        return format_response(news, "News data generated and saved successfully", 201)

    return format_response([], "No news data found", 404)


@news_bp.route("/all", methods=["POST"])
def ingest_all_news():
    """Test endpoint for all news sources. Requires: uv pip install -e jobs/"""
    # Check dependencies
    dep_check = check_scraping_dependencies()
    if dep_check:
        return dep_check

    # Get the news using GNews
    gnews_result = get_all_top_gnews()
    print("gnews done")

    # Get the news using Finviz
    finviz_result = get_all_finviz()
    print("finviz done")

    total_news = []
    total_metrics = {
        "total_articles_fetched": 0,
        "successful_scrapes": 0,
        "low_quality_skipped": 0,
        "failed_scrapes": 0,
    }

    def accumulate_metrics(metrics):
        for key in total_metrics:
            total_metrics[key] += metrics.get(key, 0)

    # Accumulate GNews data & metrics
    if isinstance(gnews_result, dict):
        total_news.extend(gnews_result["data"])
        accumulate_metrics(gnews_result["metrics"])

    # Accumulate Finviz data & metrics
    if isinstance(finviz_result, dict):
        total_news.extend(finviz_result["data"])
        accumulate_metrics(finviz_result["metrics"])

    total_scraped = total_metrics["total_articles_fetched"]
    success_rate = (
        round((total_metrics["successful_scrapes"] / total_scraped), 2)
        if total_scraped
        else 0
    )
    total_metrics["scrape_success_rate"] = success_rate

    if len(total_news) > 0:
        metrics_message = (
            f"News data generated and saved successfully | "
            f"Total: {total_metrics['total_articles_fetched']}, "
            f"Success: {total_metrics['successful_scrapes']}, "
            f"Low Quality: {total_metrics['low_quality_skipped']}, "
            f"Failed: {total_metrics['failed_scrapes']}, "
            f"Success Rate: {total_metrics['scrape_success_rate']}"
        )
        return format_response(total_news, metrics_message, 201)

    return format_response([], "No news data found", 404)


@news_bp.route("/IngestNewsOfAllEntityByGnews", methods=["POST"])
def automate_news_of_all_entity_by_gnews():
    """Test endpoint for all entities via GNews. Requires: uv pip install -e jobs/"""
    # Check dependencies
    dep_check = check_scraping_dependencies()
    if dep_check:
        return dep_check

    tickers_list = get_all_ticker_entities()

    start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = date.today().strftime("%Y-%m-%d")

    format_start_date = format_date_into_tuple_for_gnews(start_date)
    format_end_date = format_date_into_tuple_for_gnews(end_date)

    total_news = []
    total_metrics = {
        "total_articles_fetched": 0,
        "successful_scrapes": 0,
        "low_quality_skipped": 0,
        "failed_scrapes": 0,
    }

    for ticker in tickers_list:
        gnews_result = get_gnews_news_by_ticker(
            ticker, format_start_date, format_end_date
        )
        if isinstance(gnews_result, dict):
            total_news.extend(gnews_result["data"])
            for key in total_metrics:
                total_metrics[key] += gnews_result["metrics"].get(key, 0)
        print("gnews done for", ticker)
        time.sleep(10)

    total_scraped = total_metrics["total_articles_fetched"]
    success_rate = (
        round((total_metrics["successful_scrapes"] / total_scraped), 2)
        if total_scraped
        else 0
    )
    total_metrics["scrape_success_rate"] = success_rate

    if len(total_news) > 0:
        metrics_message = (
            f"News data generated and saved successfully | "
            f"Total: {total_metrics['total_articles_fetched']}, "
            f"Success: {total_metrics['successful_scrapes']}, "
            f"Low Quality: {total_metrics['low_quality_skipped']}, "
            f"Failed: {total_metrics['failed_scrapes']}, "
            f"Success Rate: {total_metrics['scrape_success_rate']}"
        )
        return format_response(total_news, metrics_message, 201)

    return format_response([], "No news data found", 404)


# ** automate news of entity and all
@news_bp.route("/IngestNewsOfEntityAndAll", methods=["POST"])
def automate_news_of_entity_and_all():
    """Test endpoint for full news ingestion. Requires: uv pip install -e jobs/"""
    # Check dependencies
    dep_check = check_scraping_dependencies()
    if dep_check:
        return dep_check

    tickers_list = get_all_ticker_entities()

    start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = date.today().strftime("%Y-%m-%d")

    format_start_date = format_date_into_tuple_for_gnews(start_date)
    format_end_date = format_date_into_tuple_for_gnews(end_date)

    total_news = []
    total_metrics = {
        "total_articles_fetched": 0,
        "successful_scrapes": 0,
        "low_quality_skipped": 0,
        "failed_scrapes": 0,
    }

    def accumulate_metrics(metrics):
        for key in total_metrics:
            total_metrics[key] += metrics.get(key, 0)

    for ticker in tickers_list:
        # GNews per ticker
        gnews_result = get_gnews_news_by_ticker(
            ticker, format_start_date, format_end_date
        )
        if isinstance(gnews_result, dict):
            total_news.extend(gnews_result["data"])
            accumulate_metrics(gnews_result["metrics"])
        print("gnews done for", ticker)

        time.sleep(10)

        # Finviz per ticker
        finviz_result = get_finviz_news_by_ticker(ticker)
        if isinstance(finviz_result, dict):
            total_news.extend(finviz_result["data"])
            accumulate_metrics(finviz_result["metrics"])
        print("finviz done for", ticker)

        time.sleep(10)

    # GNews Top
    gnews_top = get_all_top_gnews()
    if isinstance(gnews_top, dict):
        total_news.extend(gnews_top["data"])
        accumulate_metrics(gnews_top["metrics"])
    print("gnews top done")

    # Finviz All
    finviz_all = get_all_finviz()
    if isinstance(finviz_all, dict):
        total_news.extend(finviz_all["data"])
        accumulate_metrics(finviz_all["metrics"])
    print("finviz all done")

    total_scraped = total_metrics["total_articles_fetched"]
    success_rate = (
        round((total_metrics["successful_scrapes"] / total_scraped), 2)
        if total_scraped
        else 0
    )
    total_metrics["scrape_success_rate"] = success_rate

    if len(total_news) > 0:
        metrics_message = (
            f"News data generated and saved successfully | "
            f"Total: {total_metrics['total_articles_fetched']}, "
            f"Success: {total_metrics['successful_scrapes']}, "
            f"Low Quality: {total_metrics['low_quality_skipped']}, "
            f"Failed: {total_metrics['failed_scrapes']}, "
            f"Success Rate: {total_metrics['scrape_success_rate']}"
        )
        return format_response(total_news, metrics_message, 201)

    return format_response([], "No news data found", 404)


@news_bp.route("/resync", methods=["POST"])
def resync_news():
    """Resync news data"""

    # Resync news data
    result = resync_news_data()

    if result:
        return format_response(result, "News data resynced successfully", 201)

    return format_response([], "No news data found", 404)


@news_bp.route("/entity/<string:entity>", methods=["GET"])
def get_news(entity):
    """Get paginated news based on entity"""
    page = request.args.get("page", 1, type=int)  # Default to page 1
    per_page = request.args.get("per_page", 3, type=int)  # Default to 3 per page
    sort_order = request.args.get("sort_order", "desc")  # Default to ascending
    filter_time = request.args.get("filter", "all")  # Default to all-time

    news_list = news_by_ticker(entity, page, per_page, sort_order, filter_time)
    if not news_list:
        return format_response([], "News not found", 404)

    return format_response(news_list, "News fetched successfully", 200)


# ** get news based on id
@news_bp.route("/id/<uuid:id>", methods=["GET"])
def get_news_by_id(id):
    news = news_by_id(id)
    if news:
        return format_response(news, "News fetched successfully", 200)
    return format_response([], "News not found", 404)


# ** get all news
@news_bp.route("/", methods=["GET"])
def get_all_news():
    """Get paginated news"""
    page = request.args.get(
        "page", 1, type=int
    )  # Get the 'page' parameter from the request, default is 1
    per_page = request.args.get(
        "per_page", 4, type=int
    )  # Get 'per_page' parameter, default is 10

    search_term = request.args.get("search", None)  # Get search term

    # Get sorting and filtering parameters
    sort_order = request.args.get("sort_order", "desc")  # Default to ascending
    filter_time = request.args.get("filter", "all")  # Default to all-time

    news_list = all_news(page, per_page, filter_time, sort_order, search_term)

    if not news_list:
        return format_response([], "News not found", 404)
    return format_response(news_list, "News fetched successfully", 200)
