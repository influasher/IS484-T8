"""
News Processing Job - Unified Pipeline
Fetches URLs → Scrapes → Extracts Entities → Analyzes Sentiment → Saves to DB

This job is designed to run as a Kubernetes CronJob every 1-2 days.
All heavy dependencies (crawl4ai, playwright, spaCy, FinBERT) are isolated here.
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
from app.services.article_scraper import scrape_article
from app.services.sentiment_analysis import SentimentAnalyzer
from app.utils.helpers import extract_company, extract_region, extract_sector

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
    Unified News Processing Pipeline
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.sentiment_analyzer = None
        
    def initialize_services(self):
        """Initialize all heavy services (models, APIs)"""
        logger.info("Initializing sentiment analyzer...")
        self.sentiment_analyzer = SentimentAnalyzer()
        logger.info("Services initialized successfully")
        
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
        Scrape article content from URL
        
        Args:
            url: Article URL
            
        Returns:
            Dict with 'content', 'title', 'published_date' or None if failed
        """
        try:
            logger.info(f"Scraping article: {url}")
            result = await scrape_article(url)
            
            if result and result.get('content'):
                return {
                    'content': result['content'],
                    'title': result.get('title', ''),
                    'published_date': result.get('published_date'),
                    'raw_html': result.get('html', '')
                }
            else:
                logger.warning(f"No content scraped from {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return None
    
    def extract_entities_from_content(self, content: str) -> Dict[str, Any]:
        """
        Extract entities (companies, regions, sectors) from article content
        
        Args:
            content: Article text content
            
        Returns:
            Dict with 'companies', 'regions', 'sectors' lists
        """
        try:
            logger.debug("Extracting entities from content")
            
            companies = extract_company(content)
            regions = extract_region(content)
            sectors = extract_sector(content)
            
            return {
                'companies': companies if companies else [],
                'regions': regions if regions else [],
                'sectors': sectors if sectors else []
            }
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {'companies': [], 'regions': [], 'sectors': []}
    
    def analyze_sentiment(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        Analyze sentiment using ensemble of models (FinBERT, Gemini, OpenAI)
        
        Args:
            content: Article content
            title: Article title (optional)
            
        Returns:
            Dict with sentiment scores and metadata
        """
        try:
            logger.debug("Analyzing sentiment with ensemble models")
            
            # Combine title and content for analysis
            text_to_analyze = f"{title}\n\n{content}" if title else content
            
            # Get sentiment from all three models
            finbert_result = self.sentiment_analyzer.analyze_with_finbert(text_to_analyze)
            gemini_result = self.sentiment_analyzer.analyze_with_gemini(text_to_analyze)
            openai_result = self.sentiment_analyzer.analyze_with_openai(text_to_analyze)
            
            # Weighted integration for ensemble score
            ensemble_result = self.sentiment_analyzer.weighted_integration(
                finbert_result,
                gemini_result,
                openai_result
            )
            
            return {
                'finbert_score': finbert_result.get('score', 0.0),
                'finbert_sentiment': finbert_result.get('sentiment', 'neutral'),
                'second_model_score': gemini_result.get('score', 0.0),
                'second_model_sentiment': gemini_result.get('sentiment', 'neutral'),
                'third_model_score': openai_result.get('score', 0.0),
                'third_model_sentiment': openai_result.get('sentiment', 'neutral'),
                'score': ensemble_result.get('score', 0.0),  # Weighted ensemble
                'sentiment': ensemble_result.get('sentiment', 'neutral'),
                'confidence': ensemble_result.get('confidence', 0.0),
                'agreement_rate': ensemble_result.get('agreement_rate', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            # Return neutral sentiment on error
            return {
                'finbert_score': 0.0,
                'finbert_sentiment': 'neutral',
                'second_model_score': 0.0,
                'second_model_sentiment': 'neutral',
                'third_model_score': 0.0,
                'third_model_sentiment': 'neutral',
                'score': 0.0,
                'sentiment': 'neutral',
                'confidence': 0.0,
                'agreement_rate': 0.0
            }
    
    def save_to_database(
        self,
        url: str,
        title: str,
        content: str,
        published_date: Optional[datetime],
        entities: Dict[str, Any],
        sentiment: Dict[str, Any],
        entity_id: Optional[int] = None
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
                
                # Create summary (first 200 chars as placeholder)
                summary = content[:200] + "..." if len(content) > 200 else content
                
                # Create News entry
                news = News(
                    url=url,
                    title=title,
                    content=content,
                    summary=summary,
                    published_date=published_date or datetime.utcnow(),
                    scraped_at=datetime.utcnow(),
                    
                    # Entity information
                    company_names=entities.get('companies', []),
                    regions=entities.get('regions', []),
                    sectors=entities.get('sectors', []),
                    
                    # Sentiment scores
                    finbert_score=sentiment.get('finbert_score', 0.0),
                    second_model_score=sentiment.get('second_model_score', 0.0),
                    third_model_score=sentiment.get('third_model_score', 0.0),
                    score=sentiment.get('score', 0.0),  # Ensemble score
                    sentiment=sentiment.get('sentiment', 'neutral'),
                    confidence=sentiment.get('confidence', 0.0),
                    agreement_rate=sentiment.get('agreement_rate', 0.0),
                    
                    # Optional fields (add SHAP analysis if you have it)
                    shap=None,  # TODO: Add SHAP if needed
                    shapUrl=None
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
        Process a single article through the full pipeline
        
        Args:
            url_data: Dict with 'url', 'entity_name', 'entity_id', etc.
            
        Returns:
            Saved News object or None if failed
        """
        url = url_data['url']
        logger.info(f"Processing article: {url}")
        
        try:
            # Step 1: Scrape content
            scraped_data = await self.scrape_article_content(url)
            if not scraped_data:
                logger.warning(f"Skipping article (no content): {url}")
                return None
            
            # Step 2: Extract entities
            entities = self.extract_entities_from_content(scraped_data['content'])
            
            # Step 3: Analyze sentiment
            sentiment = self.analyze_sentiment(
                scraped_data['content'],
                scraped_data.get('title', '')
            )
            
            # Step 4: Save to database
            news = self.save_to_database(
                url=url,
                title=scraped_data.get('title', url_data.get('title', 'Untitled')),
                content=scraped_data['content'],
                published_date=scraped_data.get('published_date') or url_data.get('published_date'),
                entities=entities,
                sentiment=sentiment,
                entity_id=url_data.get('entity_id')
            )
            
            return news
            
        except Exception as e:
            logger.error(f"Error processing article {url}: {str(e)}")
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
            # Initialize services
            self.initialize_services()
            
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
