#!/bin/bash
set -e

# Database migrations now handled by pre-deployment job (k8s/db-migration-job.yaml)
# This ensures migrations run before any pods start, preventing crash loops on migration failures
# echo "Running database migrations..."
# .venv/bin/flask db upgrade

echo "Starting gunicorn..."
exec .venv/bin/gunicorn \
    --bind 0.0.0.0:5001 \
    --workers 4 \
    --timeout 120 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    "app:create_app()"
