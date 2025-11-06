# News Processing Microservice

## Overview

This microservice handles batch processing of news articles:
1. **Fetches URLs** from GNews API for all active entities
2. **Scrapes content** using crawl4ai + playwright
3. **Extracts entities** (companies, regions, sectors) using spaCy NER
4. **Analyzes sentiment** with ensemble of 3 models (FinBERT, Gemini, OpenAI)
5. **Generates SHAP explainability** visualizations for sentiment predictions
6. **Uploads SHAP HTML** to Azure Blob Storage (public access)
7. **Saves to database** (News table with sentiment scores + SHAP URLs)
8. **Updates SentimentHistory** with entity-level aggregated sentiment

## Architecture

- **Deployment**: Kubernetes CronJob (runs every 2 days at 2 AM UTC)
- **Memory**: 4-6Gi (all heavy models loaded)
- **Runtime**: 2-4 hours for batch processing
- **Cost**: ~50% savings vs. always-running microservice

## Prerequisites

### Azure Blob Storage Setup

The job requires Azure Blob Storage for storing SHAP HTML visualizations:

1. **Create storage account** (if not exists):
   ```bash
   az storage account create \
     --name yourstorageaccount \
     --resource-group your-resource-group \
     --location eastus \
     --sku Standard_LRS
   ```

2. **Create blob container** named `shap`:
   ```bash
   az storage container create \
     --name shap \
     --account-name yourstorageaccount \
     --public-access blob
   ```

3. **Get connection string**:
   ```bash
   az storage account show-connection-string \
     --name yourstorageaccount \
     --resource-group your-resource-group \
     --query connectionString -o tsv
   ```

4. **Add to environment variables** (see Configuration section below)

**Important:** The `shap` container must have **public blob access** so that SHAP URLs are publicly accessible.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOOKBACK_DAYS` | Number of days to look back for news | `2` |
| `MAX_ARTICLES` | Max articles to process (optional) | unlimited |
| `FLASK_ENV` | Flask environment | `production` |
| `DATABASE_URI` | PostgreSQL connection string | from secrets |
| `OPENAI_API_KEY` | OpenAI API key for sentiment analysis | from secrets |
| `GEMINI_API_KEY` | Gemini API key for sentiment analysis | from secrets |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage for SHAP HTML uploads | from secrets |

### Kubernetes Secrets Required

The CronJob requires these secrets in `sentifinance-secrets`:
- `database-url` or `database-uri`
- `db-host`, `db-port`, `db-name`, `db-user`, `db-password` (if using separate components)
- `openai-api-key`
- `gemini-api-key`
- `azure-storage-connection-string` (for SHAP HTML uploads to blob storage)

## Deployment

### Automatic (via CD Pipeline)

Changes to `Backend/jobs/*` or `Backend/Dockerfile.news-processor` will trigger:
1. Build of `news-processor` Docker image
2. Push to ACR (`sentifinancetwo.azurecr.io/news-processor:latest`)
3. Update of Kubernetes CronJob

### Manual Deployment

```bash
# Build and push image
cd Backend
docker build -f Dockerfile.news-processor -t sentifinancetwo.azurecr.io/news-processor:latest .
docker push sentifinancetwo.azurecr.io/news-processor:latest

# Apply Kubernetes manifests
kubectl apply -f k8s/news-processing-cronjob.yaml --namespace=sentifinance
```

## Testing

### Run Manual Job (Test with 10 articles)

```bash
# Create one-time job from CronJob template
kubectl create job --from=cronjob/news-processor news-processor-test \
  --namespace=sentifinance

# Or use the pre-defined manual job
kubectl apply -f k8s/news-processing-cronjob.yaml --namespace=sentifinance
kubectl delete job news-processor-manual --namespace=sentifinance --ignore-not-found
kubectl apply -f k8s/news-processing-cronjob.yaml --namespace=sentifinance

# Watch logs
kubectl logs -f job/news-processor-manual --namespace=sentifinance
```

### Local Testing

```bash
# Navigate to jobs directory
cd Backend/jobs

# Install dependencies using UV
uv sync

# Install playwright browsers
uv run playwright install chromium

# Download spaCy transformer model (required for entity extraction)
uv run python -m spacy download en_core_web_trf

# Set environment variables (or create a .env file)
export FLASK_ENV=development
export LOOKBACK_DAYS=2
export MAX_ARTICLES=5  # Limit articles for testing
export DATABASE_URI="postgresql+psycopg2://user:pass@localhost:5432/sentifinance"
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;"

# Run job
uv run python news_processing_job.py
```

**Notes:**
- The job requires ~4-6GB RAM due to heavy ML models (FinBERT, spaCy transformer, etc.)
- First run will download models (~2-3GB) which can take 10-20 minutes
- SHAP HTML files are uploaded to the `shap` container in Azure Blob Storage
- Blob container must exist and have public read access for URLs to work

## Monitoring

### Check CronJob Status

```bash
# List CronJobs
kubectl get cronjobs --namespace=sentifinance

# View CronJob details
kubectl describe cronjob news-processor --namespace=sentifinance

# List recent jobs
kubectl get jobs --namespace=sentifinance | grep news-processor
```

### View Job Logs

```bash
# List pods from jobs
kubectl get pods --namespace=sentifinance | grep news-processor

# View logs (replace with actual pod name)
kubectl logs news-processor-28401200-abcde --namespace=sentifinance

# Follow logs in real-time
kubectl logs -f news-processor-28401200-abcde --namespace=sentifinance
```

### Trigger Manual Run

```bash
# Create a one-time job from the CronJob
kubectl create job --from=cronjob/news-processor news-processor-manual-$(date +%s) \
  --namespace=sentifinance
```

## Troubleshooting

### Job Failed to Start

**Check pod status:**
```bash
kubectl get pods --namespace=sentifinance | grep news-processor
kubectl describe pod <pod-name> --namespace=sentifinance
```

**Common issues:**
- **ImagePullBackOff**: Check ACR credentials, ensure image exists
- **OOMKilled**: Increase memory limits in CronJob manifest
- **CrashLoopBackOff**: Check logs for application errors

### Database Connection Issues

**Verify secrets:**
```bash
kubectl get secret sentifinance-secrets --namespace=sentifinance -o yaml
```

**Test database connection:**
```bash
kubectl run psql-test --rm -i --tty --image postgres:15 --namespace=sentifinance \
  --env="PGPASSWORD=your-password" \
  -- psql -h your-db-host -U your-db-user -d sentifinance -c "SELECT COUNT(*) FROM news;"
```

### Model Loading Errors

**Check available memory:**
```bash
kubectl top nodes
kubectl top pods --namespace=sentifinance | grep news-processor
```

**Heavy models loaded:**
- crawl4ai: ~500MB
- playwright chromium: ~500MB
- spaCy en_core_web_trf: ~500-800MB
- FinBERT: ~400MB
- Total: ~2-2.5GB + overhead

### Job Timeout

If job exceeds 4 hours (`activeDeadlineSeconds: 14400`):
1. Reduce `LOOKBACK_DAYS`
2. Set `MAX_ARTICLES` limit
3. Increase timeout in CronJob manifest

## Schedule Configuration

Default: Every 2 days at 2 AM UTC (`0 2 */2 * *`)

**Modify schedule:**
```bash
kubectl edit cronjob news-processor --namespace=sentifinance
```

**Common cron expressions:**
- Every day at 2 AM: `0 2 * * *`
- Every 3 days at 2 AM: `0 2 */3 * *`
- Twice a week (Mon, Thu 2 AM): `0 2 * * 1,4`
- Once a week (Sunday 2 AM): `0 2 * * 0`

## Performance

### Expected Metrics

- **Articles per run**: 50-200 (depends on data sources)
- **Processing time**: 10-30 seconds per article
- **Total runtime**: 1-2 hours typical, up to 4 hours max
- **Memory usage**: 3-5GB peak
- **CPU usage**: 1-1.5 cores average

### Optimization Tips

1. **Reduce lookback period**: Lower `LOOKBACK_DAYS` for faster runs
2. **Limit articles**: Set `MAX_ARTICLES` for testing
3. **Increase parallelism**: Modify job to process multiple articles concurrently (advanced)

## Data Flow

```
┌─────────────────┐
│  GNews API      │ (Fetch URLs for active entities)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch URLs     │ (fetch_news_urls)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Scrape Content  │ (crawl4ai + playwright)
│                 │ • Fallback: description
│                 │ • Fallback: title only
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Entities│ (spaCy NER)
│                 │ • Companies
│                 │ • Regions
│                 │ • Sectors
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analyze Sentiment│ (Ensemble: FinBERT + Gemini + OpenAI)
│                 │ • Numerical score
│                 │ • Classification (bullish/bearish/neutral)
│                 │ • Confidence & agreement rate
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate SHAP   │ (Explainability for FinBERT predictions)
│                 │ • Token-level importance scores
│                 │ • Interactive HTML visualization
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Upload to Blob  │ (Azure Blob Storage)
│                 │ • Container: shap
│                 │ • Public read access
│                 │ • Returns: shapUrl
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Save to DB     │ (News table)
│                 │ • Content + entities
│                 │ • Sentiment scores
│                 │ • SHAP JSON + URL
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update History  │ (SentimentHistory aggregation by entity)
└─────────────────┘
```

## Integration with Main Backend

The main backend deployment (`sentifinance-backend`) can now:
- **Remove heavy dependencies**: crawl4ai, playwright, spaCy transformer, FinBERT
- **Reduce memory**: From 1536Mi to 512Mi
- **Serve pre-processed data**: Read from News table populated by this job

## SHAP Explainability

The job generates SHAP (SHapley Additive exPlanations) visualizations to explain sentiment predictions:

### What is SHAP?

SHAP provides token-level importance scores showing which words contributed most to the sentiment classification. This helps users understand **why** a particular sentiment was assigned.

### How it Works

1. **Generate SHAP values** using the FinBERT model
2. **Create HTML visualization** with interactive highlighting
3. **Upload to Azure Blob Storage** (container: `shap`)
4. **Save URL to database** in `News.shapUrl` field

### Example Output

- **SHAP JSON**: Stored in `News.shap` column (for programmatic access)
  ```json
  {
    "tokens": ["Tesla", "reports", "strong", "earnings", "..."],
    "shap_values": [[0.05, -0.02, ...], [0.12, 0.08, ...], ...],
    "base_values": [0.0, 0.0, ...]
  }
  ```

- **SHAP URL**: Stored in `News.shapUrl` column
  ```
  https://sentifinanceblob.blob.core.windows.net/shap/shap_explanation_a1b2c3d4e5f6.html
  ```

### Accessing SHAP Visualizations

Frontend can display SHAP explanations by:
1. Fetching `shapUrl` from News API endpoint
2. Embedding in iframe: `<iframe src="{shapUrl}" />`
3. Or opening in new tab for detailed analysis

## Support

For issues or questions:
1. Check logs: `kubectl logs <pod-name> --namespace=sentifinance`
2. Review this README
3. Check main project README and documentation
