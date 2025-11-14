from app import db
from app.models.news import News as NewsModel
from finvizfinance.quote import finvizfinance
from finvizfinance.news import News
from app.utils.helpers import get_article_details
from app.services.article_scraper import scrape_article
import pandas as pd
import time
from datetime import datetime, timedelta
from app.utils.scraping_quality import evaluate_scraping_quality


# For this service we will be using finviz to get the news
def get_finviz_news_by_ticker(query):
    try:
        stock = finvizfinance(query)
    except Exception as e:
        print(f"An error occurred: {e}")
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

    news = stock.ticker_news()

    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    news_df = pd.DataFrame(news, columns=["Date", "Title", "Link", "Source"])

    news_list = []

    # Metrics tracking
    total_count = 0
    success_count = 0
    error_count = 0
    low_quality_count = 0
    number_of_request_start = 0

    for index, row in news_df.iterrows():
        description = ""
        news_date = str(row["Date"]).split(" ")[0]

        if news_date != today and news_date != yesterday:
            continue

        total_count += 1

        try:
            if NewsModel.query.filter_by(url=row["Link"]).first():
                print("News already exists")
                continue

            print("Link:", row["Link"])

            number_of_request_start += 1
            if number_of_request_start > 15:
                print("Rate limit reached. Sleeping for 60 seconds...")
                time.sleep(60)
                number_of_request_start = 0

            article = scrape_article(row["Link"])
            if not article:
                print(f"Failed to scrape article for URL: {row['Link']}")
                error_count += 1
                continue

            article_details = get_article_details(row["Link"], article)
            if not article_details:
                print(f"Failed to get article details for URL: {row['Link']}")
                error_count += 1
                continue

            # Evaluate scraping quality
            quality_metrics = evaluate_scraping_quality(
                row["Link"], article, article_details
            )
            print("Scraping Metrics:", quality_metrics)

            if not quality_metrics["is_clean"]:
                print(f"[LOW QUALITY] Skipping article: {row['Link']}")
                low_quality_count += 1
                continue

            description = article_details["text"]
            summary = article_details["summary"]
            score = article_details["numerical_score"]
            finbert_score = article_details["finbert_score"]
            second_model_score = article_details["second_model_score"]
            third_model_score = article_details["third_model_score"]
            sentiment = article_details["classification"]
            tags = article_details["keywords"]
            confidence = article_details["confidence"]
            agreement_rate = article_details["agreement_rate"]
            company_names = article_details["companies"]
            regions = article_details["regions"]
            sectors = article_details["sectors"]

            if (
                description == "An error occurred while fetching the article details"
                or description == ""
            ):
                continue

            news_list.append(
                {
                    "published_date": row["Date"],
                    "title": row["Title"],
                    "description": description,
                    "url": row["Link"],
                    "publisher": row["Source"],
                    "ticker": query,
                    "summary": summary,
                    "score": score,
                    "finbert_score": finbert_score,
                    "second_model_score": second_model_score,
                    "third_model_score": third_model_score,
                    "sentiment": sentiment,
                    "tags": tags,
                    "confidence": confidence,
                    "agreement_rate": agreement_rate,
                    "company_names": company_names,
                    "regions": regions,
                    "sectors": sectors,
                }
            )

            news_db = NewsModel(
                publisher=row["Source"],
                description=description,
                published_date=row["Date"],
                title=row["Title"],
                url=row["Link"],
                entities=[query],
                summary=summary,
                score=score,
                finbert_score=finbert_score,
                second_model_score=second_model_score,
                third_model_score=third_model_score,
                sentiment=sentiment,
                tags=tags,
                confidence=confidence,
                agreement_rate=agreement_rate,
                company_names=company_names,
                regions=regions,
                sectors=sectors,
            )

            db.session.add(news_db)
            db.session.commit()
            success_count += 1

            print("News added to database")

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

    return {"data": news_list, "metrics": metrics}


# Get all news from finviz
def get_all_finviz():
    fnews = News()

    try:
        all_news = fnews.get_news()
    except Exception as e:
        print(f"Failed to fetch Finviz news: {e}")
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

    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    all_news_df = pd.DataFrame(
        all_news["news"], columns=["Date", "Title", "Link", "Source"]
    )

    all_news_list = []

    # Metrics
    total_count = 0
    success_count = 0
    error_count = 0
    low_quality_count = 0
    number_of_request_start = 0

    for _, row in all_news_df.iterrows():
        news_date = str(row["Date"]).split(" ")[0]

        if news_date != today and news_date != yesterday:
            continue

        total_count += 1

        try:
            if NewsModel.query.filter_by(url=row["Link"]).first():
                continue

            print("Link:", row["Link"])

            number_of_request_start += 1
            if number_of_request_start > 15:
                print("Rate limit reached. Sleeping for 60 seconds...")
                time.sleep(60)
                number_of_request_start = 0

            article = scrape_article(row["Link"])
            if not article:
                print(f"Failed to scrape article for URL: {row['Link']}")
                error_count += 1
                continue

            article_details = get_article_details(row["Link"], article)
            if not article_details:
                print(f"Failed to get article details for URL: {row['Link']}")
                error_count += 1
                continue

            # Evaluate scraping quality
            quality_metrics = evaluate_scraping_quality(
                row["Link"], article, article_details
            )
            print("Scraping Metrics:", quality_metrics)

            if not quality_metrics["is_clean"]:
                print(f"[LOW QUALITY] Skipping article: {row['Link']}")
                low_quality_count += 1
                continue

            description = article_details["text"]
            summary = article_details["summary"]
            score = article_details["numerical_score"]
            finbert_score = article_details["finbert_score"]
            second_model_score = article_details["second_model_score"]
            third_model_score = article_details["third_model_score"]
            sentiment = article_details["classification"]
            tags = article_details["keywords"]
            confidence = article_details["confidence"]
            agreement_rate = article_details["agreement_rate"]
            company_names = article_details["companies"]
            regions = article_details["regions"]
            sectors = article_details["sectors"]

            if description in [
                "",
                "An error occurred while fetching the article details",
            ]:
                continue

            all_news_list.append(
                {
                    "published_date": news_date,
                    "title": row["Title"],
                    "description": description,
                    "url": row["Link"],
                    "publisher": row["Source"],
                    "summary": summary,
                    "score": score,
                    "finbert_score": finbert_score,
                    "second_model_score": second_model_score,
                    "third_model_score": third_model_score,
                    "sentiment": sentiment,
                    "tags": tags,
                    "confidence": confidence,
                    "agreement_rate": agreement_rate,
                    "company_names": company_names,
                    "regions": regions,
                    "sectors": sectors,
                }
            )

            news_db = NewsModel(
                publisher=row["Source"],
                description=description,
                published_date=news_date,
                title=row["Title"],
                url=row["Link"],
                entities=["Top News"],
                summary=summary,
                score=score,
                finbert_score=finbert_score,
                second_model_score=second_model_score,
                third_model_score=third_model_score,
                sentiment=sentiment,
                tags=tags,
                confidence=confidence,
                agreement_rate=agreement_rate,
                company_names=company_names,
                regions=regions,
                sectors=sectors,
            )

            db.session.add(news_db)
            db.session.commit()
            success_count += 1

        except Exception as e:
            print(f"An error occurred: {e}")
            error_count += 1

    # Return news and metrics
    metrics = {
        "total_articles_fetched": total_count,
        "successful_scrapes": success_count,
        "low_quality_skipped": low_quality_count,
        "failed_scrapes": error_count,
        "scrape_success_rate": (
            round(success_count / total_count, 2) if total_count else 0
        ),
    }

    return {"data": all_news_list, "metrics": metrics}


def get_stock_fundamentals(ticker):
    stock = finvizfinance(ticker)
    fundamentals = stock.ticker_fundament()
    return fundamentals
