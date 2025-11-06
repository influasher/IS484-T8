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

3. **Configure Environment Variables:**
   - Create a `.env` file in the Backend directory:
   ```env
   FLASK_ENV=development
   FLASK_APP=run.py
   SECRET_KEY=your_secret_key
   DATABASE_URI=postgresql+psycopg2://username:password@localhost:5432/your_database
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

4. **Run Database Migrations:**
```bash
# Create a new migration (if needed)
uv run flask db migrate -m "Description of migration"

# Apply migrations to database
uv run flask db upgrade
```

5. **Run the Application:**
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

## Development Commands

### Adding New Dependencies
```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

### Running Tests
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
