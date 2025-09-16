import yfinance as yf
import requests_cache
import datetime
import time
import pandas as pd
from app import db
from app.models.news import News as NewsModel
from app.utils.helpers import get_article_details
from app.services.article_scraper import scrape_article
from app.utils.scraping_quality import evaluate_scraping_quality

def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    stock.actions
    stock_info = stock.info
    stock_price = stock_info['currentPrice']
    return stock_price

def get_performance(prices):
    start_price = prices[0]   # first available price in period
    end_price = prices[-1]    # most recent price
    return ((end_price - start_price) / start_price) * 100

def get_stock_history(ticker, period='1y'):
    """
    Get historical stock data with period support
    
    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period in yfinance format (1d, 5d, 1mo, 3mo, 6mo, 1y, ytd, 5y)
                     Defaults to '1y' to maintain backward compatibility with existing code
    
    Returns:
        dict: Dictionary containing dates and prices lists, or None if no data
    """
    try:
        print(f"Fetching {period} data for {ticker}")
        
        # Create ticker object
        stock = yf.Ticker(ticker)
        
        # Handle YTD separately if needed
        if period == 'ytd':
            # For YTD, use start and end dates
            today = datetime.datetime.now()
            start_of_year = datetime.datetime(today.year, 1, 1)
            df = stock.history(start=start_of_year, end=today)
        elif period == '1d':
            df = stock.history(period=period, interval='30m')
        elif period == '5d':
            df = stock.history(period=period, interval='1h')
        else:
            # For other periods, use the period parameter
            df = stock.history(period=period)
        
        if df.empty:
            print(f"No data found for {ticker} with period {period}")
            return None
        
        # Convert DataFrame to JSON format (same as original)
        data = {
            "dates": df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            "prices": df['Close'].tolist()
        }
        
        # Clean any NaN values
        clean_dates = []
        clean_prices = []
        
        for date, price in zip(data["dates"], data["prices"]):
            if not pd.isna(price):
                clean_dates.append(date)
                clean_prices.append(float(price))            

        performance = get_performance(clean_prices)
        
        print(f"Successfully fetched {len(clean_dates)} data points for {ticker}")
        
        return {
            "dates": clean_dates,
            "prices": clean_prices,
            "performance": performance
        }
        
    except Exception as e:
        print(f"Error fetching stock history for {ticker} with period {period}: {str(e)}")
        return None

def get_stock_news(ticker):
    stock = yf.Search(ticker, enable_fuzzy_query=True, include_cb=False)
    news = stock.news

    newslist = []

    # Metrics
    total_count = 0
    success_count = 0
    error_count = 0
    low_quality_count = 0

    rate_limit_interval = 60 / 15  # 15 requests per minute
    timeout = 60
    number_of_request_start = 0

    for news_item in news:
        total_count += 1
        link = news_item['link']
        print(link)

        try:
            if NewsModel.query.filter_by(url=link).first():
                continue

            number_of_request_start += 1
            if number_of_request_start > 15:
                print("Rate limit reached. Sleeping for 60 seconds...")
                time.sleep(timeout)
                number_of_request_start = 0

            article = scrape_article(link)
            if not article:
                print(f"Failed to scrape article for URL: {link}")
                error_count += 1
                continue

            article_details = get_article_details(link, article)
            if not article_details:
                print(f"Failed to get article details for URL: {link}")
                error_count += 1
                continue

            # Quality check
            quality_metrics = evaluate_scraping_quality(link, article, article_details)
            print("Scraping Metrics:", quality_metrics)

            if not quality_metrics["is_clean"]:
                print(f"[LOW QUALITY] Skipping article: {link}")
                low_quality_count += 1
                continue

            description = article_details['text']
            summary = article_details['summary']
            published_date = datetime.datetime.fromtimestamp(news_item["providerPublishTime"])
            title = news_item["title"]
            score = article_details['numerical_score']
            finbert_score = article_details['finbert_score']
            second_model_score = article_details['second_model_score']
            third_model_score = article_details['third_model_score']
            sentiment = article_details['classification']
            tags = article_details['keywords']
            confidence = article_details['confidence']
            agreement_rate = article_details['agreement_rate']
            company_names = article_details['companies']
            regions = article_details['regions']
            sectors = article_details['sectors']

            if description in ["", "An error occurred while fetching the article details"]:
                continue

            news_db = NewsModel(
                publisher=news_item['publisher'],
                description=description,
                published_date=published_date,
                title=title,
                url=link,
                entities=[ticker],
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
                sectors=sectors
            )

            success_count += 1

            newslist.append({
                "publisher": news_item['publisher'],
                "description": description,
                "published_date": published_date,
                "title": title,
                "url": link,
                "entities": [ticker],
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
                "sectors": sectors
            })

        except Exception as e:
            print(f"An error occurred: {e}")
            error_count += 1

    # Final metrics summary
    scrape_success_rate = round(success_count / total_count, 2) if total_count else 0
    metrics = {
        "total_articles_fetched": total_count,
        "successful_scrapes": success_count,
        "low_quality_skipped": low_quality_count,
        "failed_scrapes": error_count,
        "scrape_success_rate": scrape_success_rate
    }

    return {
        "data": newslist,
        "metrics": metrics
    }