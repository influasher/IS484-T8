# News Processing Microservice

## Overview

This microservice handles batch processing of news articles:
1. **Fetches URLs** from data sources
2. **Scrapes content** using crawl4ai + playwright
3. **Extracts entities** (companies, regions, sectors) using spaCy NER
4. **Analyzes sentiment** with ensemble of 3 models (FinBERT, Gemini, OpenAI)
5. **Saves to database** (News table with sentiment scores)
6. **Updates SentimentHistory** with entity-level aggregated sentiment

## Architecture

- **Deployment**: Kubernetes CronJob (runs every 2 days at 2 AM UTC)
- **Memory**: 4-6Gi (all heavy models loaded)
- **Runtime**: 2-4 hours for batch processing
- **Cost**: ~50% savings vs. always-running microservice

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOOKBACK_DAYS` | Number of days to look back for news | `2` |
| `MAX_ARTICLES` | Max articles to process (optional) | unlimited |
| `FLASK_ENV` | Flask environment | `production` |
| `DATABASE_URL` | PostgreSQL connection string | from secrets |
| `OPENAI_API_KEY` | OpenAI API key for sentiment | from secrets |
| `GEMINI_API_KEY` | Gemini API key for sentiment | from secrets |

### Kubernetes Secrets Required

The CronJob requires these secrets in `sentifinance-secrets`:
- `database-url`
- `db-host`, `db-port`, `db-name`, `db-user`, `db-password`
- `openai-api-key`
- `gemini-api-key`

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
cd Backend

# Set environment variables
export FLASK_ENV=development
export LOOKBACK_DAYS=2
export MAX_ARTICLES=5
export DATABASE_URL="postgresql://user:pass@localhost:5432/sentifinance"
export OPENAI_API_KEY="your-key"
export GEMINI_API_KEY="your-key"

# Install dependencies
pip install -r jobs/requirements.txt
playwright install chromium

# Run job
python jobs/news_processing_job.py
```

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
│  Data Sources   │ (Your news APIs/feeds)
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
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Entities│ (spaCy NER)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analyze Sentiment│ (FinBERT + Gemini + OpenAI)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Save to DB     │ (News table)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update History  │ (SentimentHistory aggregation)
└─────────────────┘
```

## Integration with Main Backend

The main backend deployment (`sentifinance-backend`) can now:
- **Remove heavy dependencies**: crawl4ai, playwright, spaCy transformer, FinBERT
- **Reduce memory**: From 1536Mi to 512Mi
- **Serve pre-processed data**: Read from News table populated by this job

## TODO: Integrate Data Sources

The `fetch_news_urls()` method is currently a placeholder. You need to integrate with your existing data sources:

```python
# In news_processing_job.py, update fetch_news_urls():
async def fetch_news_urls(self, lookback_days: int = 2) -> List[Dict[str, Any]]:
    # TODO: Replace with your actual implementation
    # Examples:
    # - Call news aggregation APIs (NewsAPI, Financial Times, etc.)
    # - Query RSS feeds
    # - Connect to your existing data ingestion pipeline
    
    # Return format:
    return [
        {
            'url': 'https://example.com/article-1',
            'entity_name': 'Apple Inc.',
            'entity_id': 123,
            'title': 'Apple announces...',
            'published_date': datetime(2024, 1, 15)
        },
        # ... more articles
    ]
```

## Support

For issues or questions:
1. Check logs: `kubectl logs <pod-name> --namespace=sentifinance`
2. Review this README
3. Check main project README and documentation
