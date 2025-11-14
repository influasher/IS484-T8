"""
Data validation layer for news processing job.

This module provides validation functions to ensure data integrity
before writing to the database. It prevents bad data from corrupting
the database and provides clear error messages for debugging.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# ===================================================================
# Custom Exceptions
# ===================================================================

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class DataIntegrityError(Exception):
    """Raised when data integrity constraints are violated."""
    pass


# ===================================================================
# Validation Result Classes
# ===================================================================

@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self):
        """Allow using result in boolean context."""
        return self.valid

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)


# ===================================================================
# Field Validators
# ===================================================================

def validate_ticker(ticker: str) -> ValidationResult:
    """
    Validate stock ticker symbol.

    Rules:
    - Must be 1-5 uppercase letters
    - May contain dots (e.g., BRK.A)
    - Common format: ^[A-Z]{1,5}(\.[A-Z])?$

    Args:
        ticker: Stock ticker symbol

    Returns:
        ValidationResult with any errors
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    if not ticker:
        result.add_error("Ticker cannot be empty")
        return result

    if not isinstance(ticker, str):
        result.add_error(f"Ticker must be string, got {type(ticker)}")
        return result

    # Normalize ticker (uppercase, strip whitespace)
    ticker = ticker.strip().upper()

    # Validate format
    ticker_pattern = r'^[A-Z]{1,5}(\.[A-Z])?$'
    if not re.match(ticker_pattern, ticker):
        result.add_error(
            f"Invalid ticker format: '{ticker}'. "
            f"Must be 1-5 uppercase letters, optionally followed by .X"
        )

    # Length check
    if len(ticker) > 6:  # Max 5 chars + 1 dot + 1 char
        result.add_error(f"Ticker too long: '{ticker}' (max 6 characters)")

    return result


def validate_sentiment_score(score: float) -> ValidationResult:
    """
    Validate sentiment score.

    Rules:
    - Must be a number
    - Must be between -1.0 and 1.0 (inclusive)
    - Should not be exactly 0 (indicates missing sentiment)

    Args:
        score: Sentiment score

    Returns:
        ValidationResult with any errors
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    if score is None:
        result.add_error("Sentiment score cannot be None")
        return result

    if not isinstance(score, (int, float)):
        result.add_error(f"Sentiment score must be numeric, got {type(score)}")
        return result

    if score < -1.0 or score > 1.0:
        result.add_error(
            f"Sentiment score out of range: {score}. "
            f"Must be between -1.0 and 1.0"
        )

    if score == 0.0:
        result.add_warning(
            "Sentiment score is exactly 0.0. "
            "This may indicate neutral sentiment or missing data."
        )

    return result


def validate_url(url: str) -> ValidationResult:
    """
    Validate article URL.

    Rules:
    - Must start with http:// or https://
    - Must have a domain
    - Must not exceed 2048 characters

    Args:
        url: Article URL

    Returns:
        ValidationResult with any errors
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    if not url:
        result.add_error("URL cannot be empty")
        return result

    if not isinstance(url, str):
        result.add_error(f"URL must be string, got {type(url)}")
        return result

    # Normalize URL
    url = url.strip()

    # Check protocol
    if not url.startswith(('http://', 'https://')):
        result.add_error(f"URL must start with http:// or https://: '{url}'")

    # Check length
    if len(url) > 2048:
        result.add_error(f"URL too long: {len(url)} characters (max 2048)")

    # Basic domain validation
    url_pattern = r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if not re.match(url_pattern, url):
        result.add_error(f"Invalid URL format: '{url}'")

    return result


def validate_timestamp(timestamp: Any) -> ValidationResult:
    """
    Validate timestamp.

    Rules:
    - Must be a datetime object or valid ISO string
    - Must not be in the future (beyond 1 hour grace period)
    - Must not be older than 1 year

    Args:
        timestamp: Timestamp to validate

    Returns:
        ValidationResult with any errors
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    if timestamp is None:
        result.add_error("Timestamp cannot be None")
        return result

    # Convert string to datetime if needed
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError as e:
            result.add_error(f"Invalid timestamp format: {e}")
            return result

    if not isinstance(timestamp, datetime):
        result.add_error(f"Timestamp must be datetime, got {type(timestamp)}")
        return result

    # Check if in reasonable time range
    now = datetime.now(timestamp.tzinfo)
    one_year_ago = now.replace(year=now.year - 1)
    one_hour_future = now.replace(hour=now.hour + 1)

    if timestamp > one_hour_future:
        result.add_error(
            f"Timestamp is in the future: {timestamp}. "
            f"Current time: {now}"
        )

    if timestamp < one_year_ago:
        result.add_warning(
            f"Timestamp is older than 1 year: {timestamp}. "
            f"This data may be stale."
        )

    return result


def validate_entity_name(name: str) -> ValidationResult:
    """
    Validate entity name.

    Rules:
    - Must not be empty
    - Must be 1-200 characters
    - Should not contain only special characters

    Args:
        name: Entity name

    Returns:
        ValidationResult with any errors
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    if not name:
        result.add_error("Entity name cannot be empty")
        return result

    if not isinstance(name, str):
        result.add_error(f"Entity name must be string, got {type(name)}")
        return result

    # Normalize name
    name = name.strip()

    if not name:
        result.add_error("Entity name cannot be empty after stripping whitespace")
        return result

    if len(name) > 200:
        result.add_error(f"Entity name too long: {len(name)} characters (max 200)")

    # Check if only special characters
    if not re.search(r'[a-zA-Z0-9]', name):
        result.add_error(f"Entity name must contain alphanumeric characters: '{name}'")

    return result


# ===================================================================
# Composite Validators
# ===================================================================

def validate_news_article(article: Dict[str, Any]) -> ValidationResult:
    """
    Validate a complete news article before database insertion.

    Required fields:
    - url: Article URL
    - ticker: Stock ticker
    - title: Article title
    - published_at: Publication timestamp
    - sentiment_score: Sentiment score (-1 to 1)

    Optional fields:
    - content: Article content
    - source: News source
    - entities: List of extracted entities

    Args:
        article: Article data dictionary

    Returns:
        ValidationResult with any errors/warnings
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    # Check required fields
    required_fields = ['url', 'ticker', 'title', 'published_at', 'sentiment_score']
    for field in required_fields:
        if field not in article:
            result.add_error(f"Missing required field: '{field}'")

    if not result.valid:
        return result

    # Validate individual fields
    url_result = validate_url(article['url'])
    if not url_result:
        result.errors.extend(url_result.errors)

    ticker_result = validate_ticker(article['ticker'])
    if not ticker_result:
        result.errors.extend(ticker_result.errors)

    sentiment_result = validate_sentiment_score(article['sentiment_score'])
    if not sentiment_result:
        result.errors.extend(sentiment_result.errors)
    result.warnings.extend(sentiment_result.warnings)

    timestamp_result = validate_timestamp(article['published_at'])
    if not timestamp_result:
        result.errors.extend(timestamp_result.errors)
    result.warnings.extend(timestamp_result.warnings)

    # Validate title
    if not article.get('title'):
        result.add_error("Article title cannot be empty")
    elif len(article['title']) > 500:
        result.add_error(f"Article title too long: {len(article['title'])} characters")

    # Validate optional fields
    if article.get('content') and len(article['content']) > 50000:
        result.add_warning(
            f"Article content is very long: {len(article['content'])} characters. "
            f"Consider truncating."
        )

    if article.get('source') and len(article['source']) > 100:
        result.add_error(f"Source name too long: {len(article['source'])} characters")

    # Mark as invalid if any errors
    if result.errors:
        result.valid = False

    return result


def validate_sentiment_history(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate sentiment history entry before database insertion.

    Required fields:
    - ticker: Stock ticker
    - date: Date of sentiment
    - sentiment_score: Aggregated sentiment score
    - article_count: Number of articles

    Args:
        data: Sentiment history data dictionary

    Returns:
        ValidationResult with any errors/warnings
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    # Check required fields
    required_fields = ['ticker', 'date', 'sentiment_score', 'article_count']
    for field in required_fields:
        if field not in data:
            result.add_error(f"Missing required field: '{field}'")

    if not result.valid:
        return result

    # Validate ticker
    ticker_result = validate_ticker(data['ticker'])
    if not ticker_result:
        result.errors.extend(ticker_result.errors)

    # Validate sentiment score
    sentiment_result = validate_sentiment_score(data['sentiment_score'])
    if not sentiment_result:
        result.errors.extend(sentiment_result.errors)
    result.warnings.extend(sentiment_result.warnings)

    # Validate article count
    if not isinstance(data['article_count'], int):
        result.add_error(
            f"Article count must be integer, got {type(data['article_count'])}"
        )
    elif data['article_count'] < 0:
        result.add_error(f"Article count cannot be negative: {data['article_count']}")
    elif data['article_count'] == 0:
        result.add_warning("Article count is 0. No articles for this date?")

    # Validate date
    date_result = validate_timestamp(data['date'])
    if not date_result:
        result.errors.extend(date_result.errors)

    # Mark as invalid if any errors
    if result.errors:
        result.valid = False

    return result


# ===================================================================
# Batch Validators
# ===================================================================

def validate_batch(items: List[Dict[str, Any]],
                  validator_func: callable,
                  stop_on_error: bool = False) -> List[ValidationResult]:
    """
    Validate a batch of items.

    Args:
        items: List of items to validate
        validator_func: Validation function to apply to each item
        stop_on_error: If True, stop on first error

    Returns:
        List of ValidationResults (one per item)
    """
    results = []

    for i, item in enumerate(items):
        result = validator_func(item)
        results.append(result)

        if stop_on_error and not result.valid:
            # Add error for remaining items
            for j in range(i + 1, len(items)):
                results.append(ValidationResult(
                    valid=False,
                    errors=[f"Skipped due to previous error at index {i}"],
                    warnings=[]
                ))
            break

    return results


def get_validation_summary(results: List[ValidationResult]) -> Dict[str, Any]:
    """
    Get summary statistics from validation results.

    Args:
        results: List of validation results

    Returns:
        Dictionary with summary statistics
    """
    total = len(results)
    valid = sum(1 for r in results if r.valid)
    invalid = total - valid
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)

    return {
        'total': total,
        'valid': valid,
        'invalid': invalid,
        'error_rate': invalid / total if total > 0 else 0,
        'total_errors': total_errors,
        'total_warnings': total_warnings,
    }


# ===================================================================
# Helper Functions
# ===================================================================

def sanitize_for_database(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize data before database insertion.

    - Strips whitespace from strings
    - Normalizes tickers to uppercase
    - Truncates long strings
    - Removes None values

    Args:
        data: Data dictionary

    Returns:
        Sanitized data dictionary
    """
    sanitized = {}

    for key, value in data.items():
        # Skip None values
        if value is None:
            continue

        # Strip whitespace from strings
        if isinstance(value, str):
            value = value.strip()

        # Normalize ticker
        if key == 'ticker' and isinstance(value, str):
            value = value.upper()

        # Truncate long strings
        if isinstance(value, str):
            if key == 'title' and len(value) > 500:
                value = value[:497] + '...'
            elif key == 'content' and len(value) > 50000:
                value = value[:49997] + '...'
            elif key == 'source' and len(value) > 100:
                value = value[:97] + '...'

        sanitized[key] = value

    return sanitized
