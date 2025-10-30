"""
Entity Sentiment Aggregator - Modern approach to entity sentiment calculation

Aggregates sentiment scores from recent news articles that mention each entity,
using the same sentiment analysis approach as the news processing pipeline.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sqlalchemy import and_, func

from app.models import Entity, News
from app.services.entities_service import update_entity_sentiment

logger = logging.getLogger(__name__)


class EntitySentimentAggregator:
    """
    Service for calculating entity sentiment by aggregating from recent news articles
    """

    def __init__(self, lookback_days: int = 30):
        """
        Initialize the aggregator

        Args:
            lookback_days: Number of days to look back for news articles (default: 30)
        """
        self.lookback_days = lookback_days

    def get_entity_news_articles(self, entity_ticker: str, limit: Optional[int] = None) -> List[News]:
        """
        Get recent news articles that mention the entity by ticker

        Args:
            entity_ticker: Ticker symbol of the entity to search for (e.g., "AAPL")
            limit: Maximum number of articles to return (None = no limit)

        Returns:
            List of News articles sorted by published date (newest first)
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.lookback_days)

            # Search for ticker in entities column - try multiple formats
            ticker_patterns = [
                entity_ticker,           # "AAPL"
                f"({entity_ticker})",    # "(AAPL)"
                f"{entity_ticker}:",     # "AAPL:"
            ]

            # Build query with multiple ticker format searches
            conditions = []
            for pattern in ticker_patterns:
                conditions.append(News.entities.contains([pattern]))

            # Combine conditions with OR
            from sqlalchemy import or_
            ticker_condition = or_(*conditions)

            query = News.query.filter(
                and_(
                    News.published_date >= start_date,
                    News.published_date <= end_date,
                    ticker_condition
                )
            ).order_by(News.published_date.desc())

            # Apply limit if specified
            if limit:
                query = query.limit(limit)

            articles = query.all()

            logger.info(f"Found {len(articles)} articles for ticker '{entity_ticker}' in last {self.lookback_days} days from {start_date.date()} to {end_date.date()}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching news articles for ticker {entity_ticker}: {str(e)}")
            return []

    def calculate_weighted_sentiment(self, articles: List[News]) -> Dict[str, Any]:
        """
        Calculate weighted sentiment scores from articles using multiple methods

        Args:
            articles: List of News articles with sentiment scores

        Returns:
            Dict containing all calculated sentiment metrics
        """
        if not articles:
            return self._get_empty_sentiment_result()

        # Extract sentiment data from articles
        sentiment_data = []
        for article in articles:
            if article.score is not None:  # Only include articles with sentiment scores
                sentiment_data.append({
                    'score': float(article.score),
                    'confidence': float(article.confidence or 0.7),  # Default confidence if missing
                    'published_date': article.published_date,
                    'finbert_score': float(article.finbert_score or 0),
                    'second_model_score': float(article.second_model_score or 0),
                    'third_model_score': float(article.third_model_score or 0),
                    'title': article.title,
                    'url': article.url
                })

        if not sentiment_data:
            logger.warning("No articles with sentiment scores found")
            return self._get_empty_sentiment_result()

        # Extract arrays for calculations
        scores = [item['score'] for item in sentiment_data]
        confidences = [item['confidence'] for item in sentiment_data]
        dates = [item['published_date'] for item in sentiment_data]
        finbert_scores = [item['finbert_score'] for item in sentiment_data]

        # 1. Simple Average
        simple_average = float(np.mean(scores))

        # 2. Confidence-Weighted Average
        total_confidence = sum(confidences)
        confidence_weighted = sum(
            score * confidence for score, confidence in zip(scores, confidences)
        ) / total_confidence if total_confidence > 0 else simple_average

        # 3. Time-Decay Weighted Average (recent articles weighted more heavily)
        time_weighted = self._calculate_time_weighted_average(scores, dates)

        # 4. Combined Confidence + Time Weighted Average
        combined_weighted = self._calculate_combined_weighted_average(scores, confidences, dates)

        # Use confidence-weighted as the primary score
        primary_score = confidence_weighted

        # Determine classification based on primary score
        classification = self._classify_sentiment(primary_score)

        # Calculate overall confidence (weighted by recency)
        overall_confidence = self._calculate_overall_confidence(confidences, dates)

        # Additional metrics
        score_std = float(np.std(scores)) if len(scores) > 1 else 0.0
        article_count = len(sentiment_data)

        # Date range info
        date_range = {
            'start': min(dates).isoformat(),
            'end': max(dates).isoformat(),
            'span_days': (max(dates) - min(dates)).days + 1
        }

        return {
            'sentiment_score': primary_score,
            'simple_average': simple_average,
            'confidence_weighted': confidence_weighted,
            'time_decay': time_weighted,
            'combined_weighted': combined_weighted,
            'finbert_average': float(np.mean(finbert_scores)),
            'classification': classification,
            'confidence_score': overall_confidence,
            'article_count': article_count,
            'score_std': score_std,
            'date_range': date_range,
            'raw_scores': scores,
            'recent_articles': sentiment_data[:5]  # Include 5 most recent for reference
        }

    def _calculate_time_weighted_average(self, scores: List[float], dates: List[datetime]) -> float:
        """Calculate time-decay weighted average (recent articles weighted more)"""
        if len(set(dates)) <= 1:  # All articles from same date
            return float(np.mean(scores))

        most_recent = max(dates)
        decay_factor = 0.9  # Each day older reduces weight by 10%

        weights = []
        for date in dates:
            days_old = (most_recent - date).days
            weight = decay_factor ** days_old
            weights.append(weight)

        total_weight = sum(weights)
        if total_weight == 0:
            return float(np.mean(scores))

        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        return weighted_sum / total_weight

    def _calculate_combined_weighted_average(self, scores: List[float], confidences: List[float],
                                           dates: List[datetime]) -> float:
        """Calculate combined confidence + time weighted average"""
        if len(set(dates)) <= 1:
            # If all same date, just use confidence weighting
            total_confidence = sum(confidences)
            return sum(s * c for s, c in zip(scores, confidences)) / total_confidence if total_confidence > 0 else float(np.mean(scores))

        most_recent = max(dates)
        decay_factor = 0.9

        combined_weights = []
        for confidence, date in zip(confidences, dates):
            days_old = (most_recent - date).days
            time_weight = decay_factor ** days_old
            combined_weight = confidence * time_weight
            combined_weights.append(combined_weight)

        total_weight = sum(combined_weights)
        if total_weight == 0:
            return float(np.mean(scores))

        weighted_sum = sum(score * weight for score, weight in zip(scores, combined_weights))
        return weighted_sum / total_weight

    def _calculate_overall_confidence(self, confidences: List[float], dates: List[datetime]) -> float:
        """Calculate overall confidence, giving more weight to recent articles"""
        if len(set(dates)) <= 1:
            simple_mean = float(np.mean(confidences))
            return min(0.95, max(0.1, simple_mean))  # Apply bounds

        most_recent = max(dates)
        decay_factor = 0.95  # Slower decay for confidence

        weights = []
        for date in dates:
            days_old = (most_recent - date).days
            weight = decay_factor ** days_old
            weights.append(weight)

        total_weight = sum(weights)
        if total_weight == 0:
            simple_mean = float(np.mean(confidences))
            return min(0.95, max(0.1, simple_mean))  # Apply bounds

        weighted_confidence = sum(conf * weight for conf, weight in zip(confidences, weights)) / total_weight
        return min(0.95, max(0.1, weighted_confidence))  # Bound between 0.1 and 0.95

    def _classify_sentiment(self, score: float) -> str:
        """Classify sentiment based on score"""
        if score > 10:
            return 'bullish'
        elif score < -10:
            return 'bearish'
        else:
            return 'neutral'

    def _get_empty_sentiment_result(self) -> Dict[str, Any]:
        """Return default sentiment result when no data available"""
        return {
            'sentiment_score': 0.0,
            'simple_average': 0.0,
            'confidence_weighted': 0.0,
            'time_decay': 0.0,
            'combined_weighted': 0.0,
            'finbert_average': 0.0,
            'classification': 'neutral',
            'confidence_score': 0.5,
            'article_count': 0,
            'score_std': 0.0,
            'date_range': None,
            'raw_scores': [],
            'recent_articles': []
        }

    def update_entity_sentiment(self, entity_name: str) -> Dict[str, Any]:
        """
        Calculate and update sentiment for a specific entity

        Args:
            entity_name: Name of the entity

        Returns:
            Dict with update results and calculated sentiment data
        """
        try:
            # Get entity from database
            entity = Entity.query.filter_by(name=entity_name).first()
            if not entity:
                return {
                    'success': False,
                    'error': f'Entity not found: {entity_name}',
                    'entity': None,
                    'sentiment': None
                }

            if not entity.ticker:
                return {
                    'success': False,
                    'error': f'Entity {entity_name} has no ticker',
                    'entity': {'name': entity_name, 'ticker': None},
                    'sentiment': None
                }

            # Get recent articles and calculate sentiment using ticker
            articles = self.get_entity_news_articles(entity.ticker)
            sentiment_result = self.calculate_weighted_sentiment(articles)

            # Update entity in database using existing service
            update_success = update_entity_sentiment(
                ticker=entity.ticker,
                sentiment_score=sentiment_result['sentiment_score'],
                confidence_score=sentiment_result['confidence_score'],
                time_decay_score=sentiment_result['time_decay'],
                simple_average_score=sentiment_result['simple_average'],
                classification=sentiment_result['classification']
            )

            if not update_success:
                return {
                    'success': False,
                    'error': 'Failed to update entity in database',
                    'entity': {'name': entity_name, 'ticker': entity.ticker},
                    'sentiment': sentiment_result
                }

            logger.info(f"Updated sentiment for {entity_name} ({entity.ticker}): "
                       f"{sentiment_result['classification']} "
                       f"(score: {sentiment_result['sentiment_score']:.2f}, "
                       f"articles: {sentiment_result['article_count']})")

            return {
                'success': True,
                'entity': {
                    'name': entity_name,
                    'ticker': entity.ticker,
                    'id': str(entity.id)
                },
                'sentiment': sentiment_result
            }

        except Exception as e:
            logger.error(f"Error updating entity sentiment for {entity_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'entity': None,
                'sentiment': None
            }

    def update_all_entities(self) -> Dict[str, Any]:
        """
        Update sentiment for all entities with tickers

        Returns:
            Summary of update results
        """
        try:
            # Get all entities with tickers
            entities = Entity.query.filter(
                Entity.ticker.isnot(None),
                Entity.ticker != ''
            ).all()

            if not entities:
                logger.warning("No entities with tickers found")
                return {
                    'success': True,
                    'total': 0,
                    'updated': 0,
                    'failed': 0,
                    'results': []
                }

            logger.info(f"Updating sentiment for {len(entities)} entities (lookback: {self.lookback_days} days)")

            results = []
            updated_count = 0
            failed_count = 0

            for entity in entities:
                result = self.update_entity_sentiment(entity.name)

                summary = {
                    'entity_name': entity.name,
                    'ticker': entity.ticker,
                    'success': result['success'],
                    'error': result.get('error'),
                    'article_count': result.get('sentiment', {}).get('article_count', 0) if result.get('sentiment') else 0,
                    'sentiment_score': result.get('sentiment', {}).get('sentiment_score', 0) if result.get('sentiment') else 0,
                    'classification': result.get('sentiment', {}).get('classification', 'unknown') if result.get('sentiment') else 'unknown'
                }

                results.append(summary)

                if result['success']:
                    updated_count += 1
                else:
                    failed_count += 1

            logger.info(f"Entity sentiment update complete: {updated_count} updated, {failed_count} failed")

            return {
                'success': True,
                'total': len(entities),
                'updated': updated_count,
                'failed': failed_count,
                'lookback_days': self.lookback_days,
                'results': results
            }

        except Exception as e:
            logger.error(f"Error updating all entities sentiment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'updated': 0,
                'failed': 0,
                'results': []
            }

    def get_entity_sentiment_preview(self, entity_name: str) -> Dict[str, Any]:
        """
        Preview sentiment calculation without updating database

        Args:
            entity_name: Name of the entity

        Returns:
            Preview of sentiment calculation with current vs calculated values
        """
        try:
            entity = Entity.query.filter_by(name=entity_name).first()
            if not entity:
                return {
                    'success': False,
                    'error': f'Entity not found: {entity_name}'
                }

            # Get current values from database
            current_sentiment = {
                'sentiment_score': entity.sentiment_score,
                'confidence_score': entity.confidence_score,
                'time_decay': entity.time_decay,
                'simple_average': entity.simple_average,
                'classification': entity.classification
            }

            # Calculate new values using ticker
            articles = self.get_entity_news_articles(entity.ticker)
            calculated_sentiment = self.calculate_weighted_sentiment(articles)

            return {
                'success': True,
                'entity': {
                    'name': entity_name,
                    'ticker': entity.ticker,
                    'id': str(entity.id)
                },
                'current_sentiment': current_sentiment,
                'calculated_sentiment': calculated_sentiment,
                'lookback_days': self.lookback_days,
                'would_change': (
                    abs((current_sentiment.get('sentiment_score', 0) or 0) -
                        calculated_sentiment['sentiment_score']) > 0.1
                )
            }

        except Exception as e:
            logger.error(f"Error getting sentiment preview for {entity_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Convenience functions for external use
def update_entity_sentiment_from_recent_news(entity_name: str, lookback_days: int = 30) -> Dict[str, Any]:
    """Update sentiment for a single entity"""
    aggregator = EntitySentimentAggregator(lookback_days=lookback_days)
    return aggregator.update_entity_sentiment(entity_name)


def update_all_entity_sentiments_from_recent_news(lookback_days: int = 30) -> Dict[str, Any]:
    """Update sentiment for all entities"""
    aggregator = EntitySentimentAggregator(lookback_days=lookback_days)
    return aggregator.update_all_entities()


def preview_entity_sentiment_from_recent_news(entity_name: str, lookback_days: int = 30) -> Dict[str, Any]:
    """Preview sentiment calculation without updating"""
    aggregator = EntitySentimentAggregator(lookback_days=lookback_days)
    return aggregator.get_entity_sentiment_preview(entity_name)