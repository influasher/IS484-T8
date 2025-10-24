# Data Validation Guide for News Processor

This guide explains how to use the validation layer in the news processing job to ensure data integrity.

## Overview

The `validators.py` module provides comprehensive validation functions to prevent bad data from entering the database. It validates:

- **News articles** before insertion
- **Sentiment history** entries
- **Individual fields** (ticker, URL, timestamp, etc.)
- **Batch operations** with summary statistics

## Quick Start

### Basic Usage

```python
from validators import (
    validate_news_article,
    validate_sentiment_history,
    sanitize_for_database,
    ValidationError
)

# Validate a single article
article = {
    'url': 'https://example.com/article',
    'ticker': 'AAPL',
    'title': 'Apple announces new product',
    'published_at': datetime.now(),
    'sentiment_score': 0.75,
    'content': 'Article content...',
}

result = validate_news_article(article)

if result.valid:
    # Sanitize data before insertion
    clean_data = sanitize_for_database(article)

    # Insert into database
    db.session.add(News(**clean_data))
    db.session.commit()
else:
    # Log errors
    print(f"Validation failed: {result.errors}")

    # Optionally log warnings
    if result.warnings:
        print(f"Warnings: {result.warnings}")
```

## Integration with News Processing Job

### Example: Validate Before Database Insert

Modify your `news_processing_job.py` to include validation:

```python
from validators import (
    validate_news_article,
    validate_batch,
    get_validation_summary,
    sanitize_for_database
)

def process_articles(articles):
    """Process articles with validation."""

    # Validate all articles
    results = validate_batch(articles, validate_news_article)
    summary = get_validation_summary(results)

    print(f"Validation Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Valid: {summary['valid']}")
    print(f"  Invalid: {summary['invalid']}")
    print(f"  Error Rate: {summary['error_rate']:.1%}")

    # Process only valid articles
    valid_articles = []
    for article, result in zip(articles, results):
        if result.valid:
            # Sanitize and prepare for database
            clean_article = sanitize_for_database(article)
            valid_articles.append(clean_article)
        else:
            # Log invalid articles for debugging
            print(f"Skipping invalid article: {article.get('url')}")
            print(f"  Errors: {result.errors}")

    # Bulk insert valid articles
    if valid_articles:
        try:
            db.session.bulk_insert_mappings(News, valid_articles)
            db.session.commit()
            print(f"✅ Inserted {len(valid_articles)} valid articles")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database insertion failed: {e}")

            # Retry with individual inserts for better error reporting
            inserted = 0
            for article in valid_articles:
                try:
                    db.session.add(News(**article))
                    db.session.commit()
                    inserted += 1
                except Exception as item_error:
                    db.session.rollback()
                    print(f"Failed to insert article {article.get('url')}: {item_error}")

            print(f"✅ Inserted {inserted}/{len(valid_articles)} articles individually")

    return len(valid_articles)
```

### Example: Transaction Safety

Use validation to ensure atomic transactions:

```python
def save_with_validation(article):
    """Save article with validation and transaction safety."""

    # Validate first
    result = validate_news_article(article)

    if not result.valid:
        raise ValidationError(f"Invalid article: {result.errors}")

    # Log warnings but continue
    if result.warnings:
        print(f"⚠️  Warnings for {article['url']}: {result.warnings}")

    # Sanitize
    clean_article = sanitize_for_database(article)

    # Save in transaction
    try:
        db.session.begin_nested()  # Savepoint

        news_item = News(**clean_article)
        db.session.add(news_item)
        db.session.flush()  # Get ID without committing

        # Update sentiment history
        update_sentiment_history(news_item)

        db.session.commit()
        return news_item

    except Exception as e:
        db.session.rollback()
        raise DataIntegrityError(f"Failed to save article: {e}")
```

## Validation Functions

### Individual Field Validators

#### `validate_ticker(ticker: str)`

Validates stock ticker symbols.

**Rules:**
- 1-5 uppercase letters
- May contain dot (e.g., BRK.A)
- Max 6 characters total

**Example:**
```python
result = validate_ticker("AAPL")
# ValidationResult(valid=True, errors=[], warnings=[])

result = validate_ticker("invalid_ticker")
# ValidationResult(valid=False, errors=['Invalid ticker format...'], warnings=[])
```

#### `validate_sentiment_score(score: float)`

Validates sentiment scores.

**Rules:**
- Must be between -1.0 and 1.0
- Warns if exactly 0.0 (may indicate missing data)

**Example:**
```python
result = validate_sentiment_score(0.75)
# ValidationResult(valid=True, errors=[], warnings=[])

result = validate_sentiment_score(1.5)
# ValidationResult(valid=False, errors=['Sentiment score out of range...'], warnings=[])
```

#### `validate_url(url: str)`

Validates article URLs.

**Rules:**
- Must start with http:// or https://
- Must have valid domain
- Max 2048 characters

**Example:**
```python
result = validate_url("https://example.com/article")
# ValidationResult(valid=True, errors=[], warnings=[])

result = validate_url("not-a-url")
# ValidationResult(valid=False, errors=['URL must start with http...'], warnings=[])
```

#### `validate_timestamp(timestamp: datetime)`

Validates timestamps.

**Rules:**
- Must be datetime object or ISO string
- Not in future (beyond 1 hour grace)
- Warns if older than 1 year

**Example:**
```python
result = validate_timestamp(datetime.now())
# ValidationResult(valid=True, errors=[], warnings=[])

result = validate_timestamp(datetime(2030, 1, 1))
# ValidationResult(valid=False, errors=['Timestamp is in the future...'], warnings=[])
```

### Composite Validators

#### `validate_news_article(article: Dict)`

Validates complete news article.

**Required Fields:**
- url
- ticker
- title
- published_at
- sentiment_score

**Optional Fields:**
- content
- source
- entities

#### `validate_sentiment_history(data: Dict)`

Validates sentiment history entry.

**Required Fields:**
- ticker
- date
- sentiment_score
- article_count

### Batch Validators

#### `validate_batch(items, validator_func, stop_on_error=False)`

Validates multiple items at once.

**Example:**
```python
articles = [article1, article2, article3]
results = validate_batch(articles, validate_news_article)

# Get summary
summary = get_validation_summary(results)
print(f"Valid: {summary['valid']}/{summary['total']}")
```

## Error Handling

### Validation Result Structure

```python
@dataclass
class ValidationResult:
    valid: bool          # Overall validity
    errors: List[str]    # List of error messages
    warnings: List[str]  # List of warning messages
```

### Using Results

```python
result = validate_news_article(article)

# Check validity
if result:  # or result.valid
    print("Article is valid")

# Access errors
if result.errors:
    for error in result.errors:
        print(f"ERROR: {error}")

# Access warnings
if result.warnings:
    for warning in result.warnings:
        print(f"WARNING: {warning}")
```

## Best Practices

### 1. Validate Early

Validate data as soon as it's scraped, before any processing:

```python
# ❌ Bad: Validate after processing
article = scrape_article(url)
processed = process_sentiment(article)
result = validate_news_article(processed)  # Too late!

# ✅ Good: Validate immediately
article = scrape_article(url)
result = validate_news_article(article)
if result.valid:
    processed = process_sentiment(article)
```

### 2. Use Sanitization

Always sanitize data before database insertion:

```python
clean_article = sanitize_for_database(article)
db.session.add(News(**clean_article))
```

### 3. Log Validation Failures

Keep track of what's being rejected:

```python
import logging

logger = logging.getLogger(__name__)

if not result.valid:
    logger.error(f"Validation failed for {article['url']}")
    for error in result.errors:
        logger.error(f"  - {error}")
```

### 4. Monitor Validation Metrics

Track validation rates to detect issues:

```python
# In your monitoring dashboard
validation_metrics = {
    'total_articles': len(articles),
    'valid_articles': summary['valid'],
    'invalid_articles': summary['invalid'],
    'error_rate': summary['error_rate'],
}

# Alert if error rate exceeds threshold
if summary['error_rate'] > 0.1:  # 10%
    send_alert("High validation error rate!")
```

### 5. Handle Partial Failures Gracefully

Don't let one bad article stop processing:

```python
successful = 0
failed = 0

for article in articles:
    result = validate_news_article(article)

    if result.valid:
        try:
            save_article(sanitize_for_database(article))
            successful += 1
        except Exception as e:
            logger.error(f"Failed to save: {e}")
            failed += 1
    else:
        logger.warning(f"Invalid article: {result.errors}")
        failed += 1

print(f"Processed: {successful} successful, {failed} failed")
```

## Testing

### Unit Tests Example

```python
import unittest
from validators import validate_ticker, validate_sentiment_score

class TestValidators(unittest.TestCase):

    def test_valid_ticker(self):
        result = validate_ticker("AAPL")
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_invalid_ticker_format(self):
        result = validate_ticker("invalid123")
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors), 0)

    def test_sentiment_score_in_range(self):
        result = validate_sentiment_score(0.5)
        self.assertTrue(result.valid)

    def test_sentiment_score_out_of_range(self):
        result = validate_sentiment_score(2.0)
        self.assertFalse(result.valid)
```

## Monitoring & Alerts

Add validation metrics to your monitoring dashboard:

```python
# In news_processing_job.py
import logging

# Log validation summary
logger.info(f"Validation Summary: {summary}")

# Send to monitoring system
send_metric("news_processor.validation.total", summary['total'])
send_metric("news_processor.validation.valid", summary['valid'])
send_metric("news_processor.validation.invalid", summary['invalid'])
send_metric("news_processor.validation.error_rate", summary['error_rate'])

# Alert on high error rate
if summary['error_rate'] > 0.1:
    send_alert(
        "News Processor Validation Error Rate High",
        f"Error rate: {summary['error_rate']:.1%} (threshold: 10%)"
    )
```

## Troubleshooting

### Common Validation Errors

**Error: "Sentiment score out of range"**
- Check your sentiment analysis function
- Ensure scores are normalized to [-1, 1]

**Error: "Invalid ticker format"**
- Verify ticker symbol extraction
- Check for special characters or whitespace

**Error: "URL must start with http"**
- Ensure URLs are absolute, not relative
- Add protocol if missing

**Error: "Timestamp is in the future"**
- Check system clock synchronization
- Verify timezone handling

### Debugging Failed Validations

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

result = validate_news_article(article)
if not result.valid:
    logger.debug(f"Article data: {article}")
    logger.debug(f"Validation errors: {result.errors}")
    logger.debug(f"Validation warnings: {result.warnings}")
```

## Summary

- **Always validate** before database insertion
- **Use sanitization** to clean data
- **Log failures** for debugging
- **Monitor metrics** to detect issues early
- **Handle partial failures** gracefully
- **Test validators** thoroughly
