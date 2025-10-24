FROM python:3.11-slim

# Set the working directory
WORKDIR /usr/src/app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    gcc \
    libffi-dev \
    libssl-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Install UV for fast package management
# The install script adds UV to ~/.cargo/bin, ensure PATH is set correctly
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run.py ./

# Copy the built React frontend (copied by CD workflow before Docker build)
COPY frontend-build/ ./frontend-build/

# Install dependencies with UV
# Find and use UV wherever it was installed
RUN which uv && uv sync --frozen

# Note: Heavy ML dependencies (spacy, crawl4ai, torch, transformers) have been
# removed from the backend. They are now only in the news-processor microservice.
# This reduces the backend image from ~5.8GB to ~500MB for faster deployment.

# Expose port
EXPOSE 5001

# Use production WSGI server (gunicorn) instead of Flask development server
# --bind 0.0.0.0:5001 - Listen on all interfaces
# --workers 4 - Multiple worker processes for concurrency
# --timeout 120 - Allow 2 minutes for slow requests (news scraping can take time)
# --access-logfile - - Log to stdout
# --error-logfile - - Log errors to stderr
# --preload - Load app before forking workers (faster startup, lower memory)
# "app:create_app()" - Call the app factory to get WSGI app instance
CMD [".venv/bin/gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "--preload", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
