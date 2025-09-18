import time
from gnews import GNews
from app import db
from app.models.news import News
from app.utils.helpers import URL_decoder, get_article_details
from app.services.sentiment_analysis import get_sentiment
from app.services.article_scraper import scrape_article
from datetime import datetime, timedelta
from app.utils.scraping_quality import (
    evaluate_scraping_quality,
)  # assuming you've saved the modular quality function


def insert_data_to_db(news, query):

    entities_list = [query]

    print("inserting data to db")

    n = News(
        publisher=news["publisher"]["title"],
        description=news["description"],
        published_date=news["published date"],
        title=news["title"],
        url=news["url"],
        entities=entities_list,
        summary=news["summary"],
        score=news["score"],
        finbert_score=news["finbert_score"],
        second_model_score=news["second_model_score"],
        third_model_score=news["third_model_score"],
        sentiment=news["sentiment"],
        tags=news["tags"],
        confidence=news["confidence"],
        agreement_rate=news["agreement_rate"],
        company_names=news["company_names"],
        regions=news["regions"],
        sectors=news["sectors"],
    )

    db.session.add(n)
    db.session.commit()
    return True


def check_if_data_exists(url):
    existing_news = News.query.filter_by(url=url).first()
    if existing_news:
        print("Data already exists")
        return True
    print("Data does not exist")
    return False


def get_gnews_news_by_ticker(query, start_date, end_date):
    """Fetches news articles from GNews, scrapes details, evaluates quality, and stores new articles."""

    gn = GNews(
        start_date=start_date,
        end_date=end_date,
        exclude_websites=[
            "investors.com",
            "barrons.com",
            "wsj.com",
            "bloomberg.com",
            "ft.com",
            "marketbeat.com",
            "benzinga.com",
            "streetinsider.com",
            "msn.com",
            "reuters.com",
            "uk.finance.yahoo.com",
            "seekingalpha.com",
            "fool.com",
            "GuruFocus.com",
            "mix941kmxj.com",
            "wibx950.com",
            "insidermonkey.com",
            "marketwatch.com",
            "cheap-sound.com",
            "retro1025.com",
            "wrrv.com",
            "apnnews.com",
            "fool.com",
        ],
        # max_results=1  # For testing purposes
    )

    data = gn.get_news(query)
    if not data:
        return {
            "data": [],
            "metrics": {
                "total_articles_fetched": 0,
                "successful_scrapes": 0,
                "low_quality_skipped": 0,
                "failed_scrapes": 0,
                "scrape_success_rate": 0.0,
            },
        }

    final_data = []

    # Metrics counters
    total_count = 0
    success_count = 0
    error_count = 0
    low_quality_count = 0

    number_of_request_start = 0

    for news in data:
        total_count += 1

        url = news["url"]
        decoded_url = URL_decoder(url)
        print("THIS IS THE DECODED URL", decoded_url)
        news["url"] = decoded_url["decoded_url"]

        if check_if_data_exists(news["url"]):
            continue

        number_of_request_start += 1
        if number_of_request_start > 15:
            print("Rate limit reached. Sleeping for 60 seconds...")
            time.sleep(60)
            number_of_request_start = 0

        article = scrape_article(decoded_url["decoded_url"])
        if not article:
            print(f"Failed to scrape article for URL: {decoded_url['decoded_url']}")
            error_count += 1
            continue

        article_details = get_article_details(decoded_url["decoded_url"], article)
        if not article_details:
            print(
                f"Failed to get article details for URL: {decoded_url['decoded_url']}"
            )
            error_count += 1
            continue

        quality_metrics = evaluate_scraping_quality(
            decoded_url["decoded_url"], article, article_details
        )
        print("Scraping Metrics:", quality_metrics)

        if not quality_metrics["is_clean"]:
            print(f"[LOW QUALITY] Skipping article: {decoded_url['decoded_url']}")
            low_quality_count += 1
            continue

        # Add article details to news
        news.update(
            {
                "description": article_details["text"],
                "summary": article_details["summary"],
                "score": article_details["numerical_score"],
                "finbert_score": article_details["finbert_score"],
                "second_model_score": article_details["second_model_score"],
                "third_model_score": article_details["third_model_score"],
                "confidence": article_details["confidence"],
                "sentiment": article_details["classification"],
                "agreement_rate": article_details["agreement_rate"],
                "tags": article_details["keywords"],
                "company_names": article_details["companies"],
                "regions": article_details["regions"],
                "sectors": article_details["sectors"],
            }
        )

        if news["description"] in [
            "",
            "An error occurred while fetching the article details",
        ]:
            continue

        if insert_data_to_db(news, query):
            final_data.append(news)
            success_count += 1
        else:
            print("Data not inserted")

    metrics = {
        "total_articles_fetched": total_count,
        "successful_scrapes": success_count,
        "low_quality_skipped": low_quality_count,
        "failed_scrapes": error_count,
        "scrape_success_rate": (
            round(success_count / total_count, 2) if total_count else 0
        ),
    }

    return {"data": final_data, "metrics": metrics}


## ingest data by top news
def get_all_top_gnews():
    """Fetches top news articles, filters them by recency, scrapes and evaluates quality, and stores new entries."""

    gn = GNews(
        # max_results=1,  # For testing
        exclude_websites=[
            "investors.com",
            "barrons.com",
            "wsj.com",
            "bloomberg.com",
            "ft.com",
            "marketbeat.com",
            "benzinga.com",
            "streetinsider.com",
            "msn.com",
            "reuters.com",
            "uk.finance.yahoo.com",
            "seekingalpha.com",
            "fool.com",
            "GuruFocus.com",
            "mix941kmxj.com",
            "wibx950.com",
            "insidermonkey.com",
            "marketwatch.com",
            "cheap-sound.com",
            "retro1025.com",
            "wrrv.com",
            "apnnews.com",
            "fool.com",
        ],
    )

    data = gn.get_top_news()

    if not data:
        return {
            "data": [],
            "metrics": {
                "total_articles_fetched": 0,
                "successful_scrapes": 0,
                "low_quality_skipped": 0,
                "failed_scrapes": 0,
                "scrape_success_rate": 0.0,
            },
        }

    final_data = []

    # Metrics counters
    total_count = 0
    success_count = 0
    error_count = 0
    low_quality_count = 0
    number_of_request_start = 0

    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    for news in data:
        total_count += 1

        url = news["url"]
        timestamp = news["published date"]

        dt = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
        formatted_date = dt.strftime("%Y-%m-%d")

        if formatted_date != today and formatted_date != yesterday:
            print("Date is not within the range")
            continue

        decoded_url = URL_decoder(url)
        news["url"] = decoded_url["decoded_url"]

        if check_if_data_exists(news["url"]):
            print("Data already exists")
            continue

        number_of_request_start += 1
        if number_of_request_start > 15:
            print("Rate limit reached. Sleeping for 60 seconds...")
            time.sleep(60)
            number_of_request_start = 0

        try:
            article = scrape_article(decoded_url["decoded_url"])
            if not article:
                print(f"Failed to scrape article for URL: {decoded_url['decoded_url']}")
                error_count += 1
                continue

            article_details = get_article_details(decoded_url["decoded_url"], article)
            if not article_details:
                print(
                    f"Failed to get article details for URL: {decoded_url['decoded_url']}"
                )
                error_count += 1
                continue

            # Evaluate quality
            quality_metrics = evaluate_scraping_quality(
                decoded_url["decoded_url"], article, article_details
            )
            print("Scraping Metrics:", quality_metrics)

            if not quality_metrics["is_clean"]:
                print(f"[LOW QUALITY] Skipping article: {decoded_url['decoded_url']}")
                low_quality_count += 1
                continue

            news.update(
                {
                    "description": article_details["text"],
                    "summary": article_details["summary"],
                    "score": article_details["numerical_score"],
                    "finbert_score": article_details["finbert_score"],
                    "second_model_score": article_details["second_model_score"],
                    "third_model_score": article_details["third_model_score"],
                    "sentiment": article_details["classification"],
                    "tags": article_details["keywords"],
                    "confidence": article_details["confidence"],
                    "agreement_rate": article_details["agreement_rate"],
                    "company_names": article_details["companies"],
                    "regions": article_details["regions"],
                    "sectors": article_details["sectors"],
                }
            )

            if news["description"] in [
                "",
                "An error occurred while fetching the article details",
            ]:
                continue

            if insert_data_to_db(news, "Top News"):
                final_data.append(news)
                success_count += 1
            else:
                print("Data not inserted")

        except Exception as e:
            print(f"An error occurred: {e}")
            error_count += 1

    # Final metrics summary
    metrics = {
        "total_articles_fetched": total_count,
        "successful_scrapes": success_count,
        "low_quality_skipped": low_quality_count,
        "failed_scrapes": error_count,
        "scrape_success_rate": (
            round(success_count / total_count, 2) if total_count else 0
        ),
    }

    return {"data": final_data, "metrics": metrics}
