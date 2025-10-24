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
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run.py ./

# Install dependencies with UV
RUN uv sync --frozen

# Note: Heavy ML dependencies (spacy, crawl4ai, torch, transformers) have been
# removed from the backend. They are now only in the news-processor microservice.
# This reduces the backend image from ~5.8GB to ~500MB for faster deployment.

# Expose port
EXPOSE 5001

# Your Flask app runs from run.py
# Use .venv/bin/python directly instead of 'uv run' to avoid rebuild on every start
CMD [".venv/bin/python", "run.py"]
