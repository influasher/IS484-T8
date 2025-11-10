"""
News Processing Job - Orchestrator for Original Service Pipeline

This job is designed to run as a Kubernetes CronJob every 1-2 days.
It orchestrates the existing service methods without reimplementing them.

The job performs:
1. URL fetching from GNews API for all active entities
2. Delegates to get_article_details() which handles:
   - Article scraping using crawl4ai + newspaper
   - LLM-based entity extraction (companies, regions, sectors via news_interpreter)
   - Sentiment analysis using ensemble of FinBERT + Gemini
   - SHAP explainability generation
3. Uploads SHAP visualizations to Azure Blob Storage
4. Saves all data to News table with proper field population:
   - entities: [ticker symbols]
   - company_names: [extracted company names]
   - tags: [keywords from article]
   - All sentiment scores, confidence, agreement_rate
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.config import config
from app.models import db, News, Entity, SentimentHistory
from app.services.article_scraper import scrape_article_async
# Removed unused imports: SentimentAnalyzer, extract_company, extract_region, extract_sector
# These are now only used internally by get_article_details()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NewsProcessor:
    """
    News Processing Pipeline - Orchestrator for Original Services

    This class delegates to the original service methods instead of reimplementing them.
    """

    def __init__(self, app: Flask):
        self.app = app
        # Removed: self.sentiment_analyzer - no longer needed as get_article_details() handles this
        
    async def fetch_news_urls(self, lookback_days: int = 2) -> List[Dict[str, Any]]:
        """
        Fetch URLs to process from GNews data source.
        
        Integrates with existing GNews service to fetch article URLs
        for all active entities.
        
        Args:
            lookback_days: Number of days to look back for news
            
        Returns:
            List of dicts with 'url', 'entity_name', 'entity_id' fields
        """
        logger.info(f"Fetching news URLs for the last {lookback_days} days")
        
        with self.app.app_context():
            try:
                from gnews import GNews
                from app.models.entity import Entity
                from app.utils.helpers import URL_decoder
                from datetime import datetime, timedelta
                
                # Get all active entities with tickers
                entities = Entity.query.filter(
                    Entity.ticker.isnot(None),
                    Entity.ticker != ''
                ).all()
                
                if not entities:
                    logger.warning("No entities found in database")
                    return []
                
                logger.info(f"Found {len(entities)} entities to process")
                
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=lookback_days)
                
                # Format dates for GNews (year, month, day)
                start_tuple = (start_date.year, start_date.month, start_date.day)
                end_tuple = (end_date.year, end_date.month, end_date.day)
                
                urls_to_process = []
                
                # Premium news sources (from your existing config)
                PREMIUM_SOURCES = [
                    "reuters.com",
                    "bloomberg.com",
                    "wsj.com",
                    "ft.com",
                    "marketwatch.com",
                    "cnbc.com",
                    "barrons.com"
                ]
                
                # Fetch news for each entity
                for entity in entities:
                    try:
                        # Use ticker as primary query, name as fallback
                        query = entity.ticker if entity.ticker else entity.name
                        
                        logger.info(f"Fetching news for {entity.name} ({query})")
                        
                        # Search across premium sources
                        for source in PREMIUM_SOURCES:
                            site_query = f"{query} site:{source}"
                            
                            try:
                                gn = GNews(
                                    start_date=start_tuple,
                                    end_date=end_tuple,
                                    max_results=3,
                                    language='en'
                                )
                                
                                articles = gn.get_news(site_query)
                                
                                if not articles:
                                    continue
                                
                                logger.info(f"Found {len(articles)} articles from {source} for {query}")
                                
                                for article in articles:
                                    raw_url = article.get('url')
                                    if not raw_url:
                                        continue
                                    
                                    # Decode Google News redirect URL
                                    try:
                                        decoded = URL_decoder(raw_url)
                                        url = decoded.get('decoded_url', raw_url)
                                    except:
                                        url = raw_url
                                    
                                    # Check if already processed
                                    existing = News.query.filter_by(url=url).first()
                                    if existing:
                                        logger.debug(f"Article already exists: {url}")
                                        continue
                                    
                                    # Parse published date
                                    published_date = None
                                    if article.get('published date'):
                                        try:
                                            published_date = datetime.strptime(
                                                article['published date'],
                                                '%a, %d %b %Y %H:%M:%S %Z'
                                            )
                                        except:
                                            published_date = datetime.utcnow()
                                    
                                    urls_to_process.append({
                                        'url': url,
                                        'entity_name': entity.name,
                                        'entity_id': entity.id,
                                        'ticker': query,
                                        'title': article.get('title', 'Untitled'),
                                        'publisher': article.get('publisher', {}).get('title', source),
                                        'published_date': published_date,
                                        'description': article.get('description', '')
                                    })
                                
                            except Exception as e:
                                logger.warning(f"Error fetching from {source} for {query}: {str(e)}")
                                continue
                        
                        # Rate limiting - avoid hitting API limits
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error processing entity {entity.name}: {str(e)}")
                        continue
                
                logger.info(f"Found {len(urls_to_process)} URLs to process")
                
                if len(urls_to_process) == 0:
                    logger.warning(
                        "⚠️  No new articles found. Possible reasons:\n"
                        "   - All articles already processed\n"
                        "   - No news in date range\n"
                        "   - GNews API rate limit\n"
                        "   - Network connectivity issues"
                    )
                
                return urls_to_process
                
            except Exception as e:
                logger.error(f"Error fetching news URLs: {str(e)}", exc_info=True)
                return []
    
    async def scrape_article_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape article content from URL using the ORIGINAL service implementation

        This now properly uses get_article_details() which includes:
        - Article scraping
        - LLM-based entity extraction (companies, regions, sectors)
        - Sentiment analysis with ensemble models
        - SHAP explainability generation

        Args:
            url: Article URL

        Returns:
            Dict with 'content', 'title', 'companies', 'regions', 'sectors', 'sentiment', etc.
        """
        try:
            logger.info(f"Scraping article: {url}")

            # PRE-FILTER: Skip obvious non-article URLs before scraping
            non_article_patterns = [
                '/sitemap',           # XML sitemaps
                '/investing/stock/',  # Stock ticker pages
                '/quote/',            # Stock quotes
                '/profile/company/',  # Company profiles
                '/profile/person/',   # Person profiles
                '.xml',               # XML files
                '/api/',              # API endpoints
                '/search',            # Search pages
            ]

            url_lower = url.lower()
            if any(pattern in url_lower for pattern in non_article_patterns):
                logger.warning(f"Skipping non-article URL: {url}")
                return None

            # Use the ORIGINAL scraper service (sync wrapper for async context)
            from app.services.article_scraper import scrape_article
            from app.utils.helpers import get_article_details

            # Scrape HTML using original service
            raw_html = await scrape_article_async(url)

            if not raw_html:
                logger.warning(f"No content scraped from {url}")
                return None

            # Use the ORIGINAL get_article_details helper
            # This includes: LLM entity extraction, sentiment analysis, SHAP generation
            # IMPORTANT: Wrap in try/except like the original service does (data_ingestion_gnews.py:196-201)
            try:
                details = get_article_details(url, raw_html)
            except Exception as e:
                logger.warning(f"Error getting details for {url}: {str(e)}")
                return None

            # Check if get_article_details returned error dict
            if not details or details.get('text') == "An error occurred while fetching the article details":
                logger.warning(f"Failed to extract article details from {url}")
                return None

            # QUALITY CHECK: Use the SAME quality evaluation as data_ingestion_gnews.py
            from app.utils.scraping_quality import evaluate_scraping_quality

            quality = evaluate_scraping_quality(url, raw_html, details)

            if not quality["is_clean"]:
                logger.warning(f"Low quality article skipped: {url} (reason: {quality.get('reason', 'unknown')})")
                return None

            # Return in the format expected by the rest of the pipeline
            return {
                'content': details['text'],
                'summary': details['summary'],
                'companies': details['companies'],
                'regions': details['regions'],
                'sectors': details['sectors'],
                'keywords': details['keywords'],
                'sentiment': {
                    'numerical_score': details['numerical_score'],
                    'finbert_score': details['finbert_score'],
                    'second_model_score': details['second_model_score'],
                    'third_model_score': details['third_model_score'],
                    'classification': details['classification'],
                    'confidence': details['confidence'],
                    'agreement_rate': details['agreement_rate'],
                    'shap': details['shap'],
                    'shap_html': details['shap_html']
                }
            }

        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}", exc_info=True)
            return None
    
    # REMOVED: extract_entities_from_content
    # Entity extraction is now handled by get_article_details() in scrape_article_content()
    # This uses the original news_interpreter_tagger() which combines LLM + NER extraction
    
    # REMOVED: analyze_sentiment
    # Sentiment analysis is now handled by get_article_details() in scrape_article_content()
    # This uses the original get_sentiment() function with FinBERT + Gemini ensemble
    
    def save_to_database(
        self,
        url: str,
        title: str,
        content: str,
        published_date: Optional[datetime],
        entities: Dict[str, Any],
        sentiment: Dict[str, Any],
        publisher: Optional[str] = None,
        description: Optional[str] = None,
        entity_id: Optional[int] = None,
        ticker: Optional[str] = None,
        summary: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Optional[News]:
        """
        Save processed article to database

        Args:
            url: Article URL
            title: Article title
            content: Article content
            published_date: When article was published
            entities: Extracted entities dict
            sentiment: Sentiment analysis results dict
            publisher: Article publisher/source
            description: Article description/summary from source
            entity_id: Associated entity ID (if any)

        Returns:
            Created News object or None if failed
        """
        with self.app.app_context():
            try:
                # Check if article already exists
                existing = News.query.filter_by(url=url).first()
                if existing:
                    logger.info(f"Article already exists: {url}")
                    return existing

                # Use summary from get_article_details, fallback to first 200 chars
                if not summary:
                    summary = content[:200] + "..." if len(content) > 200 else content

                # FIXED: Populate entities field with TICKER SYMBOL (following original service pattern)
                # The entities field should contain ticker symbols, NOT company names
                entities_list = []
                if ticker:
                    entities_list.append(ticker)  # Primary: Add the ticker symbol

                # Populate tags field - use keywords if available, otherwise sectors
                tags_list = keywords if keywords else entities.get('sectors', [])

                # Handle SHAP values and upload to blob storage if available
                shap_data = sentiment.get('shap')
                shap_html = sentiment.get('shap_html')
                shap_url = None

                if shap_html:
                    try:
                        from app.utils.helpers import upload_shap_to_blob
                        shap_url = upload_shap_to_blob(shap_html, url)
                        if shap_url:
                            logger.info(f"SHAP HTML uploaded to: {shap_url}")
                    except Exception as e:
                        logger.warning(f"Failed to upload SHAP HTML to blob storage: {str(e)}")

                # Create News entry
                news = News(
                    url=url,
                    title=title,
                    publisher=publisher,
                    description=description,
                    content=content,
                    summary=summary,
                    published_date=published_date or datetime.utcnow(),
                    scraped_at=datetime.utcnow(),

                    # Entity information
                    entities=entities_list if entities_list else None,
                    company_names=entities.get('companies', []),
                    regions=entities.get('regions', []),
                    sectors=entities.get('sectors', []),
                    tags=tags_list if tags_list else None,

                    # Sentiment scores (mapped from get_article_details output)
                    finbert_score=sentiment.get('finbert_score', 0.0),
                    second_model_score=sentiment.get('second_model_score', 0.0),
                    third_model_score=sentiment.get('third_model_score', 0.0),
                    score=sentiment.get('numerical_score', 0.0),  # Ensemble score from get_sentiment
                    sentiment=sentiment.get('classification', 'neutral'),  # 'bullish'/'bearish'/'neutral'
                    confidence=sentiment.get('confidence', 0.0),
                    agreement_rate=sentiment.get('agreement_rate', 0.0),

                    # SHAP explainability
                    shap=shap_data,
                    shapUrl=shap_url
                )

                db.session.add(news)
                db.session.commit()

                logger.info(f"Saved article to database: {title}")
                return news

            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error saving article: {str(e)}")
                return None
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving article to database: {str(e)}")
                return None
    
    def update_sentiment_history(self, news_articles: List[News]):
        """
        Update SentimentHistory table with entity-level aggregated sentiment
        
        Args:
            news_articles: List of processed News articles
        """
        with self.app.app_context():
            try:
                logger.info("Updating SentimentHistory with aggregated sentiment")
                
                # Group articles by entity
                from collections import defaultdict
                entity_articles = defaultdict(list)
                
                for article in news_articles:
                    # Map company names to entity IDs
                    for company_name in article.company_names or []:
                        entity = Entity.query.filter_by(name=company_name).first()
                        if entity:
                            entity_articles[entity.id].append(article)
                
                # Calculate aggregated sentiment for each entity
                for entity_id, articles in entity_articles.items():
                    if not articles:
                        continue
                    
                    # Weighted average of sentiment scores
                    total_weight = sum(a.confidence or 1.0 for a in articles)
                    weighted_score = sum(
                        (a.score or 0.0) * (a.confidence or 1.0) 
                        for a in articles
                    ) / total_weight if total_weight > 0 else 0.0
                    
                    # Determine overall sentiment
                    if weighted_score > 0.2:
                        overall_sentiment = 'positive'
                    elif weighted_score < -0.2:
                        overall_sentiment = 'negative'
                    else:
                        overall_sentiment = 'neutral'
                    
                    # Create SentimentHistory entry
                    sentiment_history = SentimentHistory(
                        entity_id=entity_id,
                        date=datetime.utcnow().date(),
                        sentiment=overall_sentiment,
                        score=weighted_score,
                        article_count=len(articles),
                        confidence=sum(a.confidence or 0.0 for a in articles) / len(articles)
                    )
                    
                    db.session.add(sentiment_history)
                
                db.session.commit()
                logger.info(f"Updated SentimentHistory for {len(entity_articles)} entities")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating sentiment history: {str(e)}")
    
    async def process_article(self, url_data: Dict[str, Any]) -> Optional[News]:
        """
        Process a single article through the full pipeline using ORIGINAL service methods

        Now properly uses get_article_details() which handles:
        - Article scraping and parsing
        - LLM-based entity extraction (companies, regions, sectors)
        - Sentiment analysis with ensemble models
        - SHAP explainability generation

        Args:
            url_data: Dict with 'url', 'entity_name', 'entity_id', 'ticker', etc.

        Returns:
            Saved News object or None if failed
        """
        url = url_data['url']
        ticker = url_data.get('ticker', '')
        logger.info(f"Processing article: {url} (ticker: {ticker})")

        try:
            # Use the ORIGINAL service implementation (scrape + get_article_details)
            # This returns ALL data: content, entities, sentiment, SHAP, etc.
            scraped_data = await self.scrape_article_content(url)

            if not scraped_data:
                logger.error(f"Skipping article (scraping failed): {url}")
                return None

            # Extract data from the original service response
            # All entity extraction and sentiment analysis is ALREADY DONE
            entities = {
                'companies': scraped_data.get('companies', []),
                'regions': scraped_data.get('regions', []),
                'sectors': scraped_data.get('sectors', [])
            }

            sentiment = scraped_data.get('sentiment', {})
            summary = scraped_data.get('summary', '')
            keywords = scraped_data.get('keywords', [])

            # Log extraction results
            logger.info(
                f"Extracted entities - Companies: {len(entities['companies'])}, "
                f"Regions: {len(entities['regions'])}, Sectors: {len(entities['sectors'])}"
            )

            # Save to database with TICKER in entities field
            news = self.save_to_database(
                url=url,
                title=url_data.get('title', 'Untitled'),
                content=scraped_data['content'],
                published_date=url_data.get('published_date'),
                entities=entities,
                sentiment=sentiment,
                publisher=url_data.get('publisher'),
                description=url_data.get('description'),
                entity_id=url_data.get('entity_id'),
                ticker=ticker,  # IMPORTANT: Pass ticker for entities field
                summary=summary,  # Use LLM-generated summary
                keywords=keywords  # Use extracted keywords for tags
            )

            return news

        except Exception as e:
            logger.error(f"Error processing article {url}: {str(e)}", exc_info=True)
            return None
    
    async def run(self, lookback_days: int = 2, max_articles: Optional[int] = None):
        """
        Run the full news processing pipeline
        
        Args:
            lookback_days: Number of days to look back for news
            max_articles: Maximum number of articles to process (None = all)
        """
        logger.info("=" * 80)
        logger.info("Starting News Processing Job")
        logger.info(f"Lookback days: {lookback_days}")
        logger.info(f"Max articles: {max_articles or 'unlimited'}")
        logger.info("=" * 80)
        
        start_time = datetime.utcnow()

        try:
            # No initialization needed - get_article_details() handles all services internally

            # Fetch URLs to process
            urls_to_process = await self.fetch_news_urls(lookback_days)
            
            if not urls_to_process:
                logger.warning("No URLs found to process")
                return
            
            # Limit if specified
            if max_articles:
                urls_to_process = urls_to_process[:max_articles]
            
            logger.info(f"Processing {len(urls_to_process)} articles")
            
            # Process articles
            processed_articles = []
            failed_count = 0
            
            for i, url_data in enumerate(urls_to_process, 1):
                logger.info(f"Article {i}/{len(urls_to_process)}")
                
                news = await self.process_article(url_data)
                
                if news:
                    processed_articles.append(news)
                else:
                    failed_count += 1
                
                # Small delay between requests to be respectful
                await asyncio.sleep(1)
            
            # Update sentiment history with aggregated data
            if processed_articles:
                self.update_sentiment_history(processed_articles)
            
            # Summary
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info("News Processing Job Completed")
            logger.info(f"Total articles processed: {len(processed_articles)}")
            logger.info(f"Failed articles: {failed_count}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Fatal error in news processing job: {str(e)}", exc_info=True)
            raise


def create_app():
    """Create Flask app for job context"""
    app = Flask(__name__)
    
    # Load configuration
    env = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    # Initialize database
    db.init_app(app)
    
    return app


async def main():
    """Main entry point for the job"""
    # Get configuration from environment
    lookback_days = int(os.getenv('LOOKBACK_DAYS', '2'))
    max_articles = os.getenv('MAX_ARTICLES')
    max_articles = int(max_articles) if max_articles else None
    
    # Create app and processor
    app = create_app()
    processor = NewsProcessor(app)
    
    # Run the pipeline
    await processor.run(lookback_days=lookback_days, max_articles=max_articles)


if __name__ == '__main__':
    asyncio.run(main())
