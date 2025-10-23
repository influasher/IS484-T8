import logging
import time

from gnews import GNews
from app import db
from app.models.news import News
from app.utils.helpers import URL_decoder, get_article_details, upload_shap_to_blob
from app.services.article_scraper import scrape_article
from datetime import datetime, timedelta
from app.utils.scraping_quality import (
    evaluate_scraping_quality,
)  # assuming you've saved the modular quality function


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("data_ingestion_gnews.log"),
            logging.StreamHandler()
        ]
    )


configure_logging()


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
        shap=news["shap"],
        shapUrl=news.get("shapUrl", None)
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


PREMIUM_SOURCES = {
    "reuters.com": {
        "reliability": 0.90, "paywall": False, "specialization": ["markets", "macro"],
        "max_results": 2, "min_text_len": 300, "min_ratio": 0.15}
    ,
    "wsj.com": {
        "reliability": 0.88, "paywall": True, "specialization": ["markets", "equities"],
        "max_results": 2, "min_text_len": 320, "min_ratio": 0.16
    },
    "ft.com": {
        "reliability": 0.90, "paywall": True, "specialization": ["global", "fx"],
        "max_results": 2, "min_text_len": 330, "min_ratio": 0.17
    },
    "bloomberg.com": {
        "reliability": 0.92, "paywall": True, "specialization": ["financial", "commodities"],
        "max_results": 2, "min_text_len": 340, "min_ratio": 0.18
    },
    "barrons.com": {
        "reliability": 0.86, "paywall": True, "specialization": ["equities", "analysis"],
        "max_results": 2, "min_text_len": 320, "min_ratio": 0.17
    },
    "marketwatch.com": {
        "reliability": 0.80, "paywall": False, "specialization": ["retail investors"],
        "max_results": 2, "min_text_len": 290, "min_ratio": 0.14
    },
    "cnbc.com": {
        "reliability": 0.78, "paywall": False, "specialization": ["breaking", "tv"],
        "max_results": 2, "min_text_len": 280, "min_ratio": 0.14
    }
    ,
    "seekingalpha.com": {
        "reliability": 0.74, "paywall": True, "specialization": ["analysis", "earnings"],
        "max_results": 2, "min_text_len": 300, "min_ratio": 0.15
    },
    "morningstar.com": {
        "reliability": 0.82, "paywall": True, "specialization": ["funds", "valuation"],
        "max_results": 2, "min_text_len": 300, "min_ratio": 0.16
    },
    "investing.com": {
        "reliability": 0.72, "paywall": False, "specialization": ["fx", "macro", "commodities"],
        "max_results": 2, "min_text_len": 270, "min_ratio": 0.13
    },
    "fortune.com": {
        "reliability": 0.78, "paywall": True, "specialization": ["corporate", "leadership"],
        "max_results": 2, "min_text_len": 300, "min_ratio": 0.15
    },
    "nikkei.com": {
        "reliability": 0.85, "paywall": True, "specialization": ["asia", "macro", "supply chain"],
        "max_results": 2, "min_text_len": 310, "min_ratio": 0.16
    },
    "economist.com": {
        "reliability": 0.90, "paywall": True, "specialization": ["macro", "geopolitics"],
        "max_results": 2, "min_text_len": 350, "min_ratio": 0.19
    }
}

EXCLUDED_SOURCES = {
    "mix941kmxj.com", "wibx950.com", "cheap-sound.com", "retro1025.com",
    "wrrv.com", "apnnews.com"
}

PAYWALL_KEY_HINTS = ["subscribe", "paywall", "premium", "metered"]  # crude heuristic


def looks_paywalled(html: str) -> bool:
    low = html.lower()
    return any(k in low for k in PAYWALL_KEY_HINTS) and len(low) < 5000  # simple heuristic


def get_premium_news_sources(query, start_date, end_date):
    metrics = {
        "total_articles_fetched": 0,
        "successful_scrapes": 0,
        "low_quality_skipped": 0,
        "failed_scrapes": 0,
        "duplicates_skipped": 0,
        "paywall_flagged": 0
    }

    final_data = []
    rate_counter = 0

    for domain, meta in PREMIUM_SOURCES.items():
        site_query = f"{query} site:{domain}"
        gn = GNews(
            start_date=start_date,
            end_date=end_date,
            max_results=meta.get("max_results", 3),
            exclude_websites=list(EXCLUDED_SOURCES)
        )

        articles = gn.get_news(site_query) or []
        metrics["total_articles_fetched"] += len(articles)

        for news in articles:
            raw_url = news.get("url")
            if not raw_url:
                continue

            decoded = URL_decoder(raw_url)
            url = decoded["decoded_url"]

            if check_if_data_exists(url):
                continue

            rate_counter += 1
            if rate_counter >= 15:
                time.sleep(60)
                rate_counter = 0

            try:
                article_html = scrape_article(url)

            except Exception as e:
                metrics["failed_scrapes"] += 1
                logging.warning("Error scraping %s: %s", url, str(e))
                continue

            if meta["paywall"] and looks_paywalled(article_html):
                metrics["paywall_flagged"] += 1
                logging.warning("Article likely paywalled, skipping: %s", url)
                continue

            try:
                details = get_article_details(url, article_html)
            except Exception as e:
                metrics["failed_scrapes"] += 1
                logging.warning("Error getting details for %s: %s", url, str(e))
                continue

            quality = evaluate_scraping_quality(
                url,
                article_html,
                details
            )

            if not quality["is_clean"]:
                metrics["low_quality_skipped"] += 1
                logging.warning("Low quality article skipped: %s", url)
                continue

            try:
                shapUrl = upload_shap_to_blob(details['shap_html'], url)
            except Exception as e:
                shapUrl = None
                logging.warning(str(e))

            news.update({
                "url": url,
                "source_metadata": {
                    "reliability": meta["reliability"],
                    "paywall": meta["paywall"],
                    "specialization": meta["specialization"]
                },
                "description": details["text"],
                "summary": details["summary"],
                "score": details["numerical_score"],
                "finbert_score": details["finbert_score"],
                "second_model_score": details["second_model_score"],
                "third_model_score": details["third_model_score"],
                "sentiment": details["classification"],
                "confidence": details["confidence"],
                "agreement_rate": details["agreement_rate"],
                "tags": details["keywords"],
                "company_names": details["companies"],
                "regions": details["regions"],
                "sectors": details["sectors"],
                "shap": details["shap"],
                "shapUrl": shapUrl
            })

            if news["description"] in ("", "An error occurred while fetching the article details"):
                ## if gemini fails
                logging.info("AI news details fetch error, skipping: %s", url)
                continue

            if insert_data_to_db(news, query):
                final_data.append(news)
                metrics["successful_scrapes"] += 1
                logging.info("Inserted article from %s: %s", domain, url)

        # Soft delay between domains to reduce burst risk
        time.sleep(4)

    metrics["scrape_success_rate"] = (
        round(metrics["successful_scrapes"] / metrics["total_articles_fetched"], 2)
        if metrics["total_articles_fetched"] else 0
    )
    return {"data": final_data, "metrics": metrics}


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
        max_results=5  # For testing purposes
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
                "shap": article_details["shap"]
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
                    "shap": article_details["shap"]
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
