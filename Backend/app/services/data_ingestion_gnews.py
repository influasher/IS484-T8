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
        logging.info(f"⏭️  Article already in database, skipping: {url}")
        return True
    logging.debug(f"Article not in database: {url}")
    return False


PREMIUM_SOURCES = {
    # ✓✓✓ TOP TIER - Free, reliable, scrapable financial news sites
    "reuters.com": {
        "reliability": 0.90, "paywall": False, "specialization": ["markets", "macro", "breaking"],
        "max_results": 4, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },
    "cnbc.com": {
        "reliability": 0.82, "paywall": False, "specialization": ["markets", "tv", "breaking"],
        "max_results": 4, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },
    "investing.com": {
        "reliability": 0.75, "paywall": False, "specialization": ["fx", "macro", "commodities", "analysis"],
        "max_results": 4, "min_text_len": 200, "min_ratio": 0.04, "enabled": True
    },

    # ✓✓ GOOD - Free business/financial news with reliable scraping
    "businessinsider.com": {
        "reliability": 0.76, "paywall": False, "specialization": ["markets", "tech", "business"],
        "max_results": 4, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },
    "finance.yahoo.com": {
        "reliability": 0.73, "paywall": False, "specialization": ["markets", "earnings", "analysis"],
        "max_results": 4, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },
    "forbes.com": {
        "reliability": 0.77, "paywall": False, "specialization": ["business", "markets", "wealth"],
        "max_results": 3, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },
    "theguardian.com": {
        "reliability": 0.83, "paywall": False, "specialization": ["business", "markets", "uk"],
        "max_results": 3, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },

    # ✓ DECENT - Generally free with occasional soft paywalls
    "marketwatch.com": {
        "reliability": 0.78, "paywall": False, "specialization": ["retail investors", "analysis"],
        "max_results": 3, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },
    "fortune.com": {
        "reliability": 0.75, "paywall": False, "specialization": ["corporate", "leadership", "tech"],
        "max_results": 2, "min_text_len": 200, "min_ratio": 0.05, "enabled": True
    },
    "thestreet.com": {
        "reliability": 0.70, "paywall": False, "specialization": ["investing", "markets", "stocks"],
        "max_results": 3, "min_text_len": 200, "min_ratio": 0.04, "enabled": True
    },

    # △ SPECIALIST - Niche but valuable when available
    "tradingeconomics.com": {
        "reliability": 0.74, "paywall": False, "specialization": ["macro", "data", "indicators"],
        "max_results": 2, "min_text_len": 200, "min_ratio": 0.04, "enabled": True
    },
    "nasdaq.com": {
        "reliability": 0.76, "paywall": False, "specialization": ["tech stocks", "markets", "ipos"],
        "max_results": 3, "min_text_len": 200, "min_ratio": 0.04, "enabled": True
    },

    # ⊗ DISABLED - Hard paywalls (kept for reference, can enable manually if needed)
    "wsj.com": {
        "reliability": 0.88, "paywall": True, "specialization": ["markets", "equities"],
        "max_results": 1, "min_text_len": 320, "min_ratio": 0.16, "enabled": False
    },
    "ft.com": {
        "reliability": 0.90, "paywall": True, "specialization": ["global", "fx"],
        "max_results": 1, "min_text_len": 330, "min_ratio": 0.17, "enabled": False
    },
    "bloomberg.com": {
        "reliability": 0.92, "paywall": True, "specialization": ["financial", "commodities"],
        "max_results": 1, "min_text_len": 340, "min_ratio": 0.18, "enabled": False
    },
    "barrons.com": {
        "reliability": 0.86, "paywall": True, "specialization": ["equities", "analysis"],
        "max_results": 1, "min_text_len": 320, "min_ratio": 0.17, "enabled": False
    },
    "seekingalpha.com": {
        "reliability": 0.74, "paywall": True, "specialization": ["analysis", "earnings"],
        "max_results": 1, "min_text_len": 300, "min_ratio": 0.15, "enabled": False
    },
    "economist.com": {
        "reliability": 0.90, "paywall": True, "specialization": ["macro", "geopolitics"],
        "max_results": 1, "min_text_len": 350, "min_ratio": 0.19, "enabled": False
    },
    "morningstar.com": {
        "reliability": 0.82, "paywall": True, "specialization": ["funds", "valuation"],
        "max_results": 1, "min_text_len": 300, "min_ratio": 0.16, "enabled": False
    },
    "nikkei.com": {
        "reliability": 0.85, "paywall": True, "specialization": ["asia", "supply chain"],
        "max_results": 1, "min_text_len": 310, "min_ratio": 0.16, "enabled": False
    }
}

EXCLUDED_SOURCES = {
    "mix941kmxj.com", "wibx950.com", "cheap-sound.com", "retro1025.com",
    "wrrv.com", "apnnews.com"
}

PAYWALL_KEY_HINTS = [
    "subscribe to continue reading",
    "become a subscriber",
    "sign up to read",
    "this article is for subscribers only",
    "paywall",
    "premium content",
    "subscriber-only",
    "subscription required",
    "unlock this article"
]

PAYWALL_URL_PATTERNS = [
    "/subscribe",
    "/subscription",
    "/paywall",
    "/register-required"
]

QUOTE_PAGE_PATTERNS = [
    "/quote/",
    "/quotes/",
    "/symbol/",
    "/symbols/",
    "/stock/",
    "/stocks/",
    "/market-data/",
    "/markets/quote/",
    "/investing/quote/",
    "/research/stocks/",
    "/chart/",
    "/charts/",
    "/ticker/"
]

QUOTE_PAGE_KEYWORDS = [
    "stock quote",
    "real-time quote",
    "delayed quote",
    "market data",
    "stock price",
    "historical data",
    "52-week high",
    "52-week low",
    "market cap",
    "price-to-earnings",
    "dividend yield",
    "volume:",
    "open:",
    "high:",
    "low:",
    "previous close:"
]


def is_quote_page(url: str, html: str | None = None) -> bool:
    """
    Detects if a URL or page content is a stock quote page rather than news.

    Checks:
    1. Quote page URL patterns
    2. High density of quote-related keywords in content
    3. Very short narrative content with lots of numeric data
    """
    # Check 1: URL patterns
    url_lower = url.lower()
    if any(pattern in url_lower for pattern in QUOTE_PAGE_PATTERNS):
        logging.debug(f"Quote page pattern detected in URL: {url}")
        return True

    # Check 2: Content analysis (if HTML provided)
    if html:
        html_lower = html.lower()
        html_len = len(html)

        # Count quote-related keywords
        keyword_matches = sum(1 for keyword in QUOTE_PAGE_KEYWORDS if keyword in html_lower)

        # High density of quote keywords suggests it's a quote page
        if keyword_matches >= 5:
            logging.debug(f"Quote page detected: {keyword_matches} quote keywords found in {url}")
            return True

        # Check for high numeric density (quote pages have lots of numbers)
        if html_len > 0:
            numeric_chars = sum(c.isdigit() or c in '.,-%$' for c in html)
            numeric_ratio = numeric_chars / html_len

            # If more than 15% of content is numbers/symbols, likely a quote page
            if numeric_ratio > 0.15 and keyword_matches >= 2:
                logging.debug(f"High numeric density ({numeric_ratio:.2%}) with quote keywords, likely quote page: {url}")
                return True

    return False


def looks_paywalled(html: str | None, url: str = "") -> bool:
    """
    Enhanced paywall detection using multiple heuristics.

    Checks:
    1. Paywall keywords in content
    2. Very short article length (< 500 chars suggests truncated content)
    3. Paywall indicators in URL
    4. Ratio of subscription-related text
    """
    if not html:
        return True  # Treat empty content as paywalled

    html_low = html.lower()
    html_len = len(html)

    # Check 1: Too short - likely paywalled/truncated
    if html_len < 500:
        logging.debug(f"Short content detected ({html_len} chars), likely paywalled")
        return True

    # Check 2: Strong paywall keywords
    keyword_matches = sum(1 for keyword in PAYWALL_KEY_HINTS if keyword in html_low)
    if keyword_matches >= 2:  # Multiple paywall indicators
        logging.debug(f"Multiple paywall keywords found ({keyword_matches})")
        return True

    # Check 3: Paywall patterns in URL
    if any(pattern in url.lower() for pattern in PAYWALL_URL_PATTERNS):
        logging.debug(f"Paywall pattern in URL: {url}")
        return True

    # Check 4: High density of subscription-related content (crude ratio)
    subscribe_count = html_low.count("subscribe") + html_low.count("subscription")
    if subscribe_count > 5 and html_len < 3000:
        logging.debug(f"High subscription keyword density ({subscribe_count} mentions)")
        return True

    return False


def get_premium_news_sources(query, start_date, end_date):
    metrics = {
        "total_articles_fetched": 0,
        "successful_scrapes": 0,
        "low_quality_skipped": 0,
        "failed_scrapes": 0,
        "duplicates_skipped": 0,
        "paywall_flagged": 0,
        "quote_pages_skipped": 0
    }

    final_data = []
    rate_counter = 0

    for domain, meta in PREMIUM_SOURCES.items():
        # Skip disabled sources (hard paywalls)
        if not meta.get("enabled", True):
            logging.info(f"⊗ Skipping {domain} - disabled (paywall/anti-bot too strong)")
            continue

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

            # Check if URL is a quote page before scraping
            if is_quote_page(url):
                metrics["quote_pages_skipped"] += 1
                logging.info(f"📊 Quote page detected, skipping: {url}")
                continue

            # New article detected - starting scrape process
            logging.info(f"🚀 Starting new scrape for: {url}")

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

            if meta["paywall"] and looks_paywalled(article_html, url):
                metrics["paywall_flagged"] += 1
                logging.warning("Article likely paywalled, skipping: %s", url)
                continue

            try:
                logging.info(f"📋 Processing article details for: {url}")
                details = get_article_details(url, article_html)

                # Check if article processing failed entirely (returns None)
                if details is None:
                    metrics["low_quality_skipped"] += 1
                    logging.warning(f"✗ Article processing failed (empty/invalid content): {url}")
                    continue

                # Check if summary was rejected by the summarizer
                if not details.get("summary"):
                    metrics["low_quality_skipped"] += 1
                    logging.warning(f"✗ Article summary rejected (likely error page): {url}")
                    continue

                logging.info(f"✓ Article details extracted successfully for: {url}")

            except Exception as e:
                metrics["failed_scrapes"] += 1
                logging.warning("✗ Error getting details for %s: %s", url, str(e))
                logging.exception(e)
                continue

            logging.info(f"🔍 Evaluating scraping quality for: {url}")
            quality = evaluate_scraping_quality(
                url,
                article_html,
                details,
                min_text_len=meta.get("min_text_len", 200),
                min_ratio=meta.get("min_ratio", 0.1)
            )

            if not quality["is_clean"]:
                metrics["low_quality_skipped"] += 1
                rejection_reason = quality.get("rejection_reason", "Unknown")
                logging.warning(f"Low quality article skipped: {url} | Reason: {rejection_reason}")
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

            logging.info(f"Attempting to insert article to DB: {url}")
            try:
                if insert_data_to_db(news, query):
                    final_data.append(news)
                    metrics["successful_scrapes"] += 1
                    logging.info("✓ Inserted article from %s: %s", domain, url)
                else:
                    logging.error(f"✗ insert_data_to_db returned False for {url}")
                    metrics["failed_scrapes"] += 1
            except Exception as e:
                logging.error(f"✗ Exception during insert_data_to_db for {url}: {str(e)}")
                logging.exception(e)
                metrics["failed_scrapes"] += 1

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
    quote_pages_count = 0

    number_of_request_start = 0

    for news in data:
        total_count += 1

        url = news["url"]
        decoded_url = URL_decoder(url)
        print("THIS IS THE DECODED URL", decoded_url)
        news["url"] = decoded_url["decoded_url"]

        if check_if_data_exists(news["url"]):
            continue

        # Check if URL is a quote page before scraping
        if is_quote_page(news["url"]):
            quote_pages_count += 1
            logging.info(f"📊 Quote page detected, skipping: {news['url']}")
            continue

        # New article detected - starting scrape process
        logging.info(f"🚀 Starting new scrape for: {decoded_url['decoded_url']}")

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
    quote_pages_count = 0
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

        # Check if URL is a quote page before scraping
        if is_quote_page(news["url"]):
            quote_pages_count += 1
            logging.info(f"📊 Quote page detected, skipping: {news['url']}")
            continue

        # New article detected - starting scrape process
        logging.info(f"🚀 Starting new scrape for: {decoded_url['decoded_url']}")

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
