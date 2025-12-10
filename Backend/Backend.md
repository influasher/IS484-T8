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
