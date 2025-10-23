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

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run.py ./

# Install dependencies with UV
RUN uv sync --frozen

# Download spacy model and setup crawl4ai
RUN uv run python -m spacy download en_core_web_trf || echo "Spacy model download failed"
RUN uv run crawl4ai-setup || echo "Crawl4AI setup failed"

# Expose port
EXPOSE 5001

# Your Flask app runs from run.py
# Use .venv/bin/python directly instead of 'uv run' to avoid rebuild on every start
CMD [".venv/bin/python", "run.py"]
