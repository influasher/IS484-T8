# Flask-Based News and Sentiment Analysis Tool

## Overview

This project is a Flask-based application that automates the ingestion, processing, and analysis of news.

## Features

- User Authentication: Secure registration, login, and session management using JWT. (Not yet implemented on the frontend)
- News Aggregation: Fetch and summarize news articles by entity.
- News Tagging: Analyze the news and tag the company, sector and region
- Sentiment Analysis: Provide sentiment scores for categorized news
- PDF Report: Generate PDF report based on the entity and news related to it

## Tech Stack
Backend:
- Flask
- Flask-JWT-Extended (for authentication)
- SQLAlchemy (ORM for database management)
- Alembic (for database migrations)

Database:
- PostgreSQL

Package Management:
- UV (ultrafast Python package installer and resolver)

## Project Structure

```
Backend/
├── app/
│   ├── models/               # Database models
│   │   ├── user.py           # User and UserOTP models
│   │   ├── news.py           # News model
│   │   ├── entity.py         # Entity model
│   │   ├── sentiment_history.py  # SentimentHistory model
│   │   ├── client_portfolio.py   # ClientPortfolio model
│   │   ├── client_performance.py # ClientPerformance model
│   │   ├── client_preferences.py # ClientPreferences model
│   │   ├── feedback.py       # Feedback model
│   │   ├── transactions.py   # Transactions model
│   │   └── __init__.py
│   ├── routes/               # API endpoints (blueprints)
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── user.py           # User management endpoints
│   │   ├── news.py           # News endpoints
│   │   ├── entities.py       # Entity endpoints
│   │   ├── sentiment_analysis.py  # Sentiment analysis endpoints
│   │   ├── sentiment_history.py   # Sentiment history endpoints
│   │   ├── portfolio.py      # Portfolio management endpoints
│   │   ├── transactions.py   # Transaction endpoints
│   │   ├── recommendations.py # Recommendation endpoints
│   │   ├── feedback.py       # Feedback endpoints
│   │   ├── pdf.py            # PDF generation endpoints
│   │   └── __init__.py
│   ├── services/             # Business logic for data processing
│   │   ├── sentiment_analysis.py      # ML sentiment analysis service
│   │   ├── entity_sentiment_analyzer.py # Entity-specific sentiment
│   │   ├── news_services.py           # News processing services
│   │   ├── entities_service.py        # Entity management services
│   │   ├── sentiment_history_services.py # Sentiment history services
│   │   ├── portfolio_service.py       # Portfolio management
│   │   ├── recommendation_service.py  # Investment recommendations
│   │   ├── feedback_services.py       # Feedback processing
│   │   ├── data_ingestion_gnews.py    # GNews API integration
│   │   ├── data_ingestion_finviz.py   # Finviz scraping
│   │   ├── data_ingestion_yfinance.py # Yahoo Finance integration
│   │   ├── article_scraper.py         # Web scraping service
│   │   ├── email_service.py           # Email notifications
│   │   ├── export_pdf.py              # PDF export service
│   │   ├── email_pdf.py               # Email PDF service
│   │   ├── recommendation_pdf.py      # Recommendation PDF generation
│   │   └── __init__.py
│   ├── utils/                # Utility functions and helpers
│   │   ├── db_scripts/       # Database utility scripts
│   │   │   ├── seed_users.py
│   │   │   ├── seed_news.py
│   │   │   ├── seed_entities.py
│   │   │   ├── clear_users.py
│   │   │   ├── clear_news.py
│   │   │   ├── clear_entities.py
│   │   │   └── create_missing_preferences.py
│   │   ├── helpers.py        # General helper functions
│   │   ├── helpers_constants.py # Constants and configurations
│   │   ├── validators.py     # Input validation functions
│   │   ├── decorators.py     # Custom decorators (auth, etc.)
│   │   ├── scraping_quality.py # Scraping quality checks
│   │   └── __init__.py
│   ├── __init__.py           # Flask app initialization
│   └── config.py             # Configuration settings
├── jobs/                     # Background job processors
│   ├── news_processing_job.py     # Main news processing job
│   ├── validators.py              # Job-specific validators
│   ├── NEWS-JOB-README.md         # Job documentation
│   ├── VALIDATION_GUIDE.md        # Validation guide
│   ├── pyproject.toml             # Job dependencies
│   ├── uv.lock                    # Job locked dependencies
│   ├── requirements.txt           # Job requirements
│   ├── temp_pdfs/                 # Temporary PDF storage for jobs
│   └── __init__.py
├── migrations/               # Alembic migration files
│   ├── versions/             # Migration version files
│   └── env.py                # Migration environment config
├── tests/                    # Unit and integration tests
│   ├── test_models/          # Model tests
│   ├── test_routes/          # Route tests
│   ├── test_services/        # Service tests
│   ├── test_data/            # Test data fixtures
│   ├── conftest.py           # Pytest configuration
│   └── run_tests.py          # Test runner
├── temp_pdfs/                # Temporary PDF storage
├── instance/                 # Flask instance folder
├── .env                      # Environment variables
├── .coveragerc               # Coverage configuration
├── Backend.md                # Project documentation
├── pyproject.toml            # Python project configuration and dependencies
├── uv.lock                   # Locked dependency versions
├── requirements.txt          # Requirements file
├── Dockerfile                # Docker container configuration for main app
├── Dockerfile.news-processor # Docker container for news processor job
├── entrypoint.sh             # Docker entrypoint script
├── compose.yaml              # Docker Compose configuration
└── run.py                    # Entry point for running the app
```

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- UV package manager (install from: https://docs.astral.sh/uv/getting-started/installation/)

## Setup and Installation

1. **Clone the Repository:**
```bash
git clone https://github.com/influasher/IS484-T8
cd IS484-T2/Backend
```

2. **Install Dependencies using UV:**
```bash
# Install UV if you haven't already
# For macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# For Windows:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install project dependencies
uv sync
```

3. **Database Setup:**

   **Prerequisites:**
   - PostgreSQL 12+ installed and running
   - Database user with CREATE DATABASE privileges

   **Create Database:**
   ```sql
   -- Connect to PostgreSQL as superuser and run:
   CREATE DATABASE sentifinance;
   CREATE USER sentifinance_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE sentifinance TO sentifinance_user;
   ```

4. **Configure Environment Variables:**
   - Create a `.env` file in the Backend directory:
   ```env
   FLASK_ENV=development
   FLASK_APP=run.py
   SECRET_KEY=your_secret_key
   DATABASE_URI=postgresql+psycopg2://sentifinance_user:your_password@localhost:5432/sentifinance
   JWT_SECRET_KEY=your_jwt_secret_key
   LOG_LEVEL=DEBUG
   APP_DEBUG=True
   APP_PORT=5001

   # API Keys
   GEMINI_API_KEY=your_GEMINI_AI_key
   GEMINI_API_KEY_SW=another_GEMINI_AI_key
   OPENAI_API_KEY=your_open_AI_key

   # Email Configuration
   MAIL_USERNAME=your_email
   MAIL_PASSWORD=password_from_gmail_app_key

   # Azure Storage (for SHAP HTML uploads)
   AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string
   ```

5. **Database Migrations:**

   We use `Flask-Migrate` (Alembic) to manage database schema versions. This ensures schema changes are tracked and reproducible across environments.

   **Important Notes:**
   - `Flask-Migrate` compares the current database schema with SQLAlchemy models to detect differences
   - Changes to the database in development **must** be done through migrations
   - Alembic cannot detect all changes automatically - see [limitations here](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect)

   **Initial Setup:**
   ```bash
   # Apply migrations to create all tables
   uv run flask db upgrade
   ```

   **Working with Migrations:**
   ```bash
   # View current migration version
   uv run flask db current

   # Update to latest version
   uv run flask db upgrade

   # Generate new migration (when you modify models)
   uv run flask db migrate -m "Description of changes"

   # Generate blank migration (if alembic doesn't detect changes)
   uv run flask db revision

   # Rollback migrations
   uv run flask db downgrade               # Previous version
   uv run flask db downgrade <version_id>  # Specific version
   ```

6. **Database Utility Scripts:**

   Use these scripts for seeding and managing database data:

   ```bash
   # Seed entities (companies/stocks)
   uv run python -c "from app.utils.db_scripts.seed_entities import seed_entities; seed_entities()"

   # Seed S&P 500 entities
   uv run python -c "from app.utils.db_scripts.seed_sp500_entities import seed_sp500_entities; seed_sp500_entities()"

   # Seed sample users
   uv run python -c "from app.utils.db_scripts.seed_users import seed_users; seed_users()"

   # Seed sample news data
   uv run python -c "from app.utils.db_scripts.seed_news import seed_news; seed_news()"

   # Create missing user preferences
   uv run python -c "from app.utils.db_scripts.create_missing_preferences import create_missing_preferences; create_missing_preferences()"

   # Clear data (for development/testing)
   uv run python -c "from app.utils.db_scripts.clear_entities import clear_entities; clear_entities()"
   uv run python -c "from app.utils.db_scripts.clear_users import clear_users; clear_users()"
   uv run python -c "from app.utils.db_scripts.clear_news import clear_news; clear_news()"
   ```

7. **Run the Application:**
```bash
# Run the Flask backend API
uv run python run.py
```

## Running the News-Processor Job

The news-processor job handles batch processing of news articles with ML-based sentiment analysis and SHAP explainability. See [jobs/README.md](jobs/README.md) for detailed documentation.

### Quick Start (Local Testing)

```bash
# Navigate to jobs directory
cd jobs

# Install dependencies (separate from main backend)
uv sync

# Install playwright browsers
uv run playwright install chromium

# Download spaCy model
uv run python -m spacy download en_core_web_trf

# Set environment variables (or use .env file)
export FLASK_ENV=development
export DATABASE_URI="postgresql+psycopg2://user:pass@localhost:5432/dbname"
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export AZURE_STORAGE_CONNECTION_STRING="your-azure-storage-connection-string"
export LOOKBACK_DAYS=2
export MAX_ARTICLES=5  # Limit for testing

# Run the job
uv run python news_processing_job.py
```

### What the Job Does

1. Fetches news URLs from GNews API for all active entities
2. Scrapes article content using crawl4ai + playwright
3. Extracts entities (companies, regions, sectors) using spaCy NER
4. Analyzes sentiment with ensemble of 3 models (FinBERT, Gemini, OpenAI)
5. Generates SHAP explainability visualizations
6. Uploads SHAP HTML to Azure Blob Storage
7. Saves all data to News table with sentiment scores and SHAP URLs
8. Updates SentimentHistory with entity-level aggregated sentiment

**Note:** The job requires significant memory (4-6GB) due to heavy ML models. For production, it runs as a Kubernetes CronJob. See [jobs/README.md](jobs/README.md) for deployment details.

## Web Scraping Implementation

The application uses advanced web scraping techniques to extract full article content from news URLs. This section explains how the scraping system works.

### Overview

The web scraping system is built on top of two main technologies:
- **Crawl4AI**: A Python library optimized for LLM-friendly web scraping
- **Playwright**: A browser automation framework that handles JavaScript-heavy websites

### How It Works

**File Location:** `app/services/article_scraper.py`

The scraper is designed to handle various website types, from simple static HTML to complex JavaScript-rendered pages.

#### Basic Flow

1. **URL Validation**: Checks if URL is valid and accessible
2. **Content Extraction**: Uses Crawl4AI with Playwright to fetch article content
3. **HTML Cleaning**: Removes ads, navigation, and other non-article content
4. **Text Extraction**: Extracts clean text suitable for NLP analysis
5. **Quality Check**: Validates that extracted content meets minimum quality standards

#### Implementation Details

```python
from crawl4ai import AsyncWebCrawler
from app.services.article_scraper import scrape_article

# Basic usage
article_data = await scrape_article(url="https://example.com/news-article")

# Returns:
# {
#     'url': 'https://example.com/news-article',
#     'title': 'Article Title',
#     'content': 'Full article text...',
#     'published_date': '2024-01-15',
#     'success': True
# }
```

### Configuration

**Playwright Browser Setup:**

The scraper requires Playwright's Chromium browser to be installed:

```bash
# Install Playwright browsers
uv run playwright install chromium

# Or install all browsers
uv run playwright install
```

**Scraping Parameters:**

The scraper can be configured with various parameters:

```python
# In app/services/article_scraper.py
SCRAPER_CONFIG = {
    'timeout': 30000,           # Max wait time (ms)
    'wait_for': 'networkidle',  # Wait until network is idle
    'headless': True,           # Run browser in headless mode
    'user_agent': 'Mozilla/5.0...',  # Custom user agent
}
```

### Quality Assurance

**File Location:** `app/utils/scraping_quality.py`

The system includes quality checks to ensure scraped content is usable:

1. **Length Validation**: Article must have minimum word count
2. **Content Ratio**: Text-to-HTML ratio must exceed threshold
3. **Noise Detection**: Filters out navigation, ads, and boilerplate text
4. **Language Detection**: Ensures content is in expected language

```python
from app.utils.scraping_quality import validate_scraped_content

is_valid, quality_score = validate_scraped_content(
    content=article_text,
    min_words=100,
    min_quality_score=0.6
)
```

### Handling Different Website Types

**Static HTML Sites:**
- Fast extraction using HTML parsing
- No JavaScript rendering needed
- Example: Traditional news sites, blogs

**JavaScript-Heavy Sites:**
- Full browser rendering with Playwright
- Waits for dynamic content to load
- Example: Modern SPAs, React-based news sites

**Paywalled Content:**
- Detects paywall presence
- Extracts available preview text
- Marks article as partial content

### Error Handling

The scraper implements robust error handling:

```python
# Common error scenarios
try:
    article = await scrape_article(url)
except TimeoutError:
    # Site took too long to load
    logger.warning(f"Timeout scraping {url}")
except InvalidURLError:
    # URL is malformed or inaccessible
    logger.error(f"Invalid URL: {url}")
except ScrapingQualityError:
    # Content quality too low
    logger.info(f"Low quality content from {url}")
```

### Performance Optimization

**Concurrency:**
The news processing job scrapes multiple articles in parallel:

```python
# In jobs/news_processing_job.py
async def process_articles_batch(urls):
    async with AsyncWebCrawler() as crawler:
        tasks = [scrape_article(url, crawler) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Rate Limiting:**
Built-in delays prevent overwhelming target websites:
- Respects robots.txt directives
- Implements exponential backoff on failures
- Randomizes request timing

**Caching:**
Successfully scraped articles are cached to avoid re-scraping:
- Stored in PostgreSQL News table
- TTL-based invalidation
- Cache key includes URL + scrape timestamp

### Troubleshooting

**Issue: Playwright not installed**
```bash
# Solution
uv run playwright install chromium
```

**Issue: Scraping timeouts**
```python
# Increase timeout in article_scraper.py
SCRAPER_CONFIG['timeout'] = 60000  # 60 seconds
```

**Issue: JavaScript not rendering**
```python
# Force wait for specific selector
await crawler.wait_for_selector('.article-content')
```

**Issue: Getting blocked by websites**
```python
# Rotate user agents, add delays
SCRAPER_CONFIG['user_agent'] = 'Custom-Bot/1.0'
await asyncio.sleep(random.uniform(1, 3))
```

## SHAP Explainability Implementation

The application uses SHAP (SHapley Additive exPlanations) to provide interpretable explanations for sentiment analysis predictions. This helps users understand why a particular sentiment score was assigned to an article.

### Overview

**What is SHAP?**

SHAP is a game-theoretic approach to explain machine learning model predictions. It calculates how much each feature (word/phrase) contributes to the final sentiment prediction.

- **Red values**: Features pushing sentiment toward negative
- **Blue values**: Features pushing sentiment toward positive
- **Magnitude**: How strongly the feature influences the prediction

### How It Works

**File Location:** `app/services/sentiment_analysis.py`

The SHAP implementation is integrated into the sentiment analysis pipeline:

1. **Model Prediction**: Ensemble model generates sentiment score
2. **SHAP Calculation**: Compute feature importance for the prediction
3. **Visualization**: Generate interactive HTML chart
4. **Storage**: Upload HTML to Azure Blob Storage
5. **Database**: Store URL reference in News table

### Implementation Details

#### SHAP Value Generation

```python
from transformers import pipeline
import shap

# Initialize sentiment model
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    tokenizer="ProsusAI/finbert"
)

# Create SHAP explainer
explainer = shap.Explainer(sentiment_pipeline)

# Generate SHAP values
article_text = "The company reported strong earnings..."
shap_values = explainer([article_text])

# SHAP values array shows contribution of each token
# Shape: (1, num_tokens, num_classes)
```

#### Visualization Creation

```python
import shap

# Create SHAP force plot (shows token-level contributions)
shap.plots.text(shap_values[0])

# Or create waterfall plot (shows cumulative contributions)
shap.plots.waterfall(shap_values[0])

# Save to HTML file
html_output = shap.plots.text(shap_values[0], display=False)
with open('shap_explanation.html', 'w') as f:
    f.write(html_output)
```

### Azure Blob Storage Integration

SHAP visualizations are stored in Azure Blob Storage for efficient delivery:

**File Location:** `jobs/news_processing_job.py`

```python
from azure.storage.blob import BlobServiceClient

# Initialize Azure client
connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_name = "shap-explanations"

# Upload SHAP HTML
blob_name = f"shap_{news_id}_{timestamp}.html"
blob_client = blob_service_client.get_blob_client(
    container=container_name,
    blob=blob_name
)

with open('shap_explanation.html', 'rb') as data:
    blob_client.upload_blob(data, overwrite=True)

# Get public URL
shap_url = blob_client.url

# Store in database
news.shap_url = shap_url
db.session.commit()
```

### Configuration

**Environment Variables:**

```env
# Required for SHAP upload
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
```

**Azure Storage Setup:**

```bash
# Create storage account (if not exists)
az storage account create \
  --name sentifinancestorage \
  --resource-group sentifinance-rg \
  --location eastus \
  --sku Standard_LRS

# Create container for SHAP files
az storage container create \
  --name shap-explanations \
  --account-name sentifinancestorage \
  --public-access blob

# Get connection string
az storage account show-connection-string \
  --name sentifinancestorage \
  --resource-group sentifinance-rg
```

### Model-Specific SHAP Implementation

The application uses an ensemble of three models, each with SHAP explanations:

#### 1. FinBERT SHAP
```python
# Financial domain-specific BERT model
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")

# SHAP for transformer models
explainer = shap.Explainer(model, tokenizer)
shap_values = explainer([article_text])
```

#### 2. Gemini SHAP (Proxy Method)
```python
# For API-based models, use perturbation method
import google.generativeai as genai

def gemini_predict(texts):
    model = genai.GenerativeModel('gemini-pro')
    results = []
    for text in texts:
        response = model.generate_content(f"Analyze sentiment: {text}")
        # Parse sentiment score from response
        score = parse_sentiment_score(response.text)
        results.append(score)
    return results

# Use masker for perturbation-based SHAP
masker = shap.maskers.Text(tokenizer=r'\W+')
explainer = shap.Explainer(gemini_predict, masker=masker)
shap_values = explainer([article_text])
```

#### 3. OpenAI SHAP (Proxy Method)
```python
# Similar to Gemini, use perturbation
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def openai_predict(texts):
    results = []
    for text in texts:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"Rate sentiment from -1 (negative) to 1 (positive): {text}"
            }]
        )
        score = float(response.choices[0].message.content)
        results.append(score)
    return results

masker = shap.maskers.Text(tokenizer=r'\W+')
explainer = shap.Explainer(openai_predict, masker=masker)
shap_values = explainer([article_text])
```

### Ensemble SHAP Aggregation

The final SHAP visualization combines all three models:

```python
# Average SHAP values across models
finbert_shap = explainer_finbert([text])
gemini_shap = explainer_gemini([text])
openai_shap = explainer_openai([text])

# Align token positions (models may tokenize differently)
aligned_shap = align_shap_values([finbert_shap, gemini_shap, openai_shap])

# Weighted average based on model confidence
ensemble_shap = (
    0.4 * aligned_shap['finbert'] +
    0.3 * aligned_shap['gemini'] +
    0.3 * aligned_shap['openai']
)

# Generate final visualization
shap.plots.text(ensemble_shap)
```

### Optimization & Caching

SHAP calculation is computationally expensive. Optimizations include:

**Background Processing:**
```python
# SHAP generation happens in async job, not in API request
# See jobs/news_processing_job.py
async def generate_shap_async(news_id, article_text):
    shap_values = await compute_shap(article_text)
    html = generate_shap_html(shap_values)
    url = await upload_to_azure(html, news_id)
    await update_database(news_id, shap_url=url)
```

**Token Limiting:**
```python
# Truncate long articles to reduce computation
MAX_TOKENS = 512  # FinBERT max input length

def truncate_for_shap(text, max_tokens=512):
    tokens = tokenizer.encode(text, truncation=True, max_length=max_tokens)
    return tokenizer.decode(tokens)
```

**Batch Processing:**
```python
# Process multiple articles in batch
explainer = shap.Explainer(model, tokenizer)
shap_values = explainer(list_of_articles)  # Vectorized computation
```

### Accessing SHAP Visualizations

**Via API:**
```bash
# Get news with SHAP URL
curl http://localhost:5001/news/123

# Response includes:
{
  "id": 123,
  "title": "Company Reports Earnings",
  "sentiment": 0.85,
  "shap_url": "https://sentifinancestorage.blob.core.windows.net/shap-explanations/shap_123_20240115.html",
  ...
}
```

**Frontend Integration:**
```javascript
// Display SHAP in iframe
<iframe
  src={news.shap_url}
  width="100%"
  height="400px"
  title="SHAP Explanation"
/>
```

### Troubleshooting

**Issue: SHAP computation takes too long**
```python
# Solution: Reduce max tokens or use sampling
explainer = shap.Explainer(model, tokenizer, max_evals=100)
```

**Issue: Azure upload fails**
```python
# Check connection string and container permissions
az storage container show-permission \
  --name shap-explanations \
  --account-name sentifinancestorage
```

**Issue: SHAP values inconsistent**
```python
# Ensure consistent random seed
import numpy as np
np.random.seed(42)
```

**Issue: Out of memory during SHAP**
```python
# Process in smaller batches
batch_size = 5
for i in range(0, len(articles), batch_size):
    batch = articles[i:i+batch_size]
    shap_values = explainer(batch)
    save_shap_results(shap_values)
```

### Further Reading

- [SHAP Documentation](https://shap.readthedocs.io/)
- [SHAP for Transformers](https://shap.readthedocs.io/en/latest/example_notebooks/api_examples/models/Transformers.html)
- [Azure Blob Storage Python SDK](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)

## Azure Communication Services Setup

The application uses Azure Communication Services (ACS) for sending OTP emails during passwordless authentication. Follow these steps to set up ACS:

### 1. Create Azure Communication Services Resource

**Using Azure Portal:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → Search "Communication Services"
3. Fill in the details:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Use existing (e.g., `sentifinance.azurecr.io`)
   - **Resource Name**: `sentifinance-communication`
   - **Region**: Same as your other resources (e.g., East US)
4. Click "Review + Create" → "Create"

**Using Azure CLI:**
```bash
# Create Communication Services resource
az communication create \
  --name sentifinance-communication \
  --resource-group sentifinance.azurecr.io \
  --location eastus
```

### 2. Get Connection String

**Via Azure Portal:**
1. Go to your Communication Services resource
2. Navigate to "Settings" → "Keys"
3. Copy the "Primary connection string"

**Via Azure CLI:**
```bash
# Get connection string
az communication list-key \
  --name sentifinance-communication \
  --resource-group sentifinance.azurecr.io
```

### 3. Set Up Email Domain

**Option A: Use Azure-managed domain (Quick Start)**
1. In your Communication Services resource, go to "Email" → "Provision domains"
2. Select "Add a free Azure subdomain"
3. Choose a subdomain (e.g., `sentifinance-12345.azurecomm.net`)
4. Wait for provisioning to complete
5. Your sender email will be: `DoNotReply@sentifinance-12345.azurecomm.net`

**Option B: Use custom domain (Production)**
1. Go to "Email" → "Provision domains" → "Add a custom domain"
2. Enter your domain (e.g., `notifications.yourdomain.com`)
3. Add required DNS records to your domain:
   ```
   Type: TXT
   Name: @
   Value: ms-domain-verification=<verification-code>

   Type: TXT
   Name: @
   Value: v=spf1 include:spf.protection.outlook.com -all

   Type: CNAME
   Name: selector1._domainkey
   Value: <dkim-value-1>

   Type: CNAME
   Name: selector2._domainkey
   Value: <dkim-value-2>
   ```
4. Click "Verify" after DNS propagation
5. Your sender email will be: `noreply@notifications.yourdomain.com`

### 4. Connect Email Domain to Communication Services

1. In Communication Services resource, go to "Email" → "Manage domains"
2. Click on your domain → "Connect domain"
3. Select your Communication Services resource
4. Save the configuration

### 5. Configure Environment Variables

Add these variables to your `.env` file:

```env
# Azure Communication Services
AZURE_COMMUNICATION_CONNECTION_STRING=endpoint=https://sentifinance-communication.communication.azure.com/;accesskey=your-access-key
AZURE_EMAIL_SENDER=DoNotReply@sentifinance-12345.azurecomm.net
```

### 6. Test Email Configuration

**Test via Backend:**
```bash
# Start the backend
uv run python run.py

# Test OTP email (replace with valid user email)
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Test via Azure CLI:**
```bash
# Send test email
az communication email send \
  --connection-string "$AZURE_COMMUNICATION_CONNECTION_STRING" \
  --sender "DoNotReply@sentifinance-12345.azurecomm.net" \
  --to "test@example.com" \
  --subject "Test Email" \
  --body "This is a test email from ACS"
```

### 7. Production Considerations

**Security:**
- Store connection string in Azure Key Vault (not plain text)
- Use managed identities when possible
- Implement rate limiting for email sending

**Monitoring:**
- Enable logging in Communication Services
- Set up alerts for email delivery failures
- Monitor email quota usage

**DNS Configuration for Custom Domains:**
- Use a subdomain (e.g., `mail.yourdomain.com`) for better deliverability
- Implement DMARC policy for email authentication
- Monitor SPF/DKIM alignment

**Troubleshooting Common Issues:**

| Issue | Solution |
|-------|----------|
| DNS verification fails | Wait up to 24 hours for DNS propagation |
| Emails not delivered | Check spam folders, verify sender reputation |
| Connection string invalid | Regenerate keys in Azure Portal |
| Domain verification pending | Ensure all DNS records are correctly configured |
| Rate limiting errors | Implement exponential backoff in email service |

### 8. Bypass OTP for Testing (Development Only)

For local development when you don't want to set up ACS, you can enable console logging of OTP codes:

**Modify `app/services/email_service.py`:**

```python
class EmailService:
    def __init__(self):
        # Check for development bypass mode
        self.development_mode = (
            os.getenv('FLASK_ENV') == 'development' and
            os.getenv('BYPASS_OTP_EMAIL', 'false').lower() == 'true'
        )

        if self.development_mode:
            print("⚠️  EMAIL BYPASS MODE ENABLED - OTPs will be logged to console")
            return

        # Original ACS configuration
        connection_string = os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING')
        # ... rest of existing __init__ code

    def send_otp_email(self, recipient_email: str, otp_code: str, user_name: str = None) -> bool:
        if self.development_mode:
            print(f"""
            ===============================================
            🔑 DEVELOPMENT OTP (NOT SENT TO EMAIL)
            ===============================================
            Recipient: {recipient_email}
            User: {user_name or 'Unknown'}
            OTP Code: {otp_code}
            Expires: 24 hours
            ===============================================
            """)
            return True

        # Original email sending logic continues here...
```

**Add to your `.env` file:**

```env
# For development testing without ACS
BYPASS_OTP_EMAIL=true
```

**Testing workflow:**

```bash
# 1. Start backend with bypass enabled
uv run python run.py

# 2. Request OTP (check console for the code)
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "existing-user@example.com"}'

# 3. Use the OTP from console output to verify
curl -X POST http://localhost:5001/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"otp_code": "123456"}'
```

**⚠️ Important:** Remove `BYPASS_OTP_EMAIL=true` before production deployment.

## Development Commands

### Adding New Dependencies
```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

### Running Tests
Integration testing done with local Postgres.
Add `TEST_DATABASE_URI` as an environment variable.
```bash
# Run all tests
uv run python -m tests.run_tests

# Run with coverage
uv run python -m tests.run_tests coverage
```

### Database Migrations
```bash
# Create a new migration
uv run flask db migrate -m "Description of migration"

# Apply migrations
uv run flask db upgrade

# Downgrade migrations
uv run flask db downgrade
```
