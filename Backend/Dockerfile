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
COPY entrypoint.sh ./

# Copy the built React frontend (copied by CD workflow before Docker build)
COPY frontend-build/ ./frontend-build/

# Install dependencies with UV
# Find and use UV wherever it was installed
RUN which uv && uv sync --frozen

# Note: Heavy ML dependencies (spacy, crawl4ai, torch, transformers) have been
# removed from the backend. They are now only in the news-processor microservice.
# This reduces the backend image from ~5.8GB to ~500MB for faster deployment.

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 5001

# Use entrypoint script to run migrations before starting gunicorn
CMD ["./entrypoint.sh"]
