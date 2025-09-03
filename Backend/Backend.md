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
│   ├── routes/               # API endpoints (blueprints)
│   ├── services/             # Business logic for data processing
│   ├── utils/                # Utility functions and helpers
│   ├── __init__.py           # Flask app initialization
│   └── config.py             # Configuration settings
├── migrations/               # Alembic migration files
├── tests/                    # Unit and integration tests
├── temp_pdfs/                # Temporary PDF storage
├── .env                      # Environment variables
├── .gitignore                # Exclude files from commit
├── Backend.md                # Project documentation
├── pyproject.toml            # Python project configuration and dependencies
├── uv.lock                   # Locked dependency versions
├── Dockerfile                # Docker container configuration
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
   GEMINI_API_KEY=your_GEMINI_AI_key
   GEMINI_API_KEY_SW=another_GEMINI_AI_key
   OPEN_AI_KEY=your_open_AI_key
   MAIL_USERNAME=your_email
   MAIL_PASSWORD=password_from_gmail_app_key
   ```

4. Run Database Migrations:
    - Ensure Liquibase is installed and configured
    - Navigate to the migrations directory:
    - Run Backend\migrations\db\create_db.sql in Postgres to create the Database
    - Run migration:

    ```
    liquibase update
    ```
5. setup crawl4ai:
```

6. **Run the Application:**
```bash
uv run python run.py
```

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
uv run pytest

# Run with coverage
uv run coverage run -m pytest
uv run coverage report
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
