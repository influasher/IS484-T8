# Azure Container Instances (ACI) Configuration Guide

Comprehensive guide for configuring Azure Container Instances for the news-processor batch job workload.

---

## Overview

The news-processor runs as a Kubernetes CronJob deployed to Azure Container Instances (ACI) via the Virtual Kubelet provider. This guide covers optimal configurations for your specific workload characteristics:

**Workload Profile:**
- **Type**: Batch processing (ML inference)
- **Schedule**: Every 2 days at 2 AM UTC
- **Duration**: 2-4 hours per run
- **Resource Needs**: 3-5GB RAM, 1-2 vCPUs
- **Failure Tolerance**: Can tolerate interruptions (stateless, idempotent)

---

## 1. Spot vs. Regular Instances

### Spot Instances (Recommended - Current Config)

**What are Spot Instances?**
- Azure's excess capacity offered at discounted prices (up to 70-80% cheaper)
- Can be evicted if Azure needs the capacity for pay-as-you-go workloads
- Best for interruptible, fault-tolerant workloads

**Cost Comparison:**

| Instance Type | Cost per GB/hour | Monthly Cost (80 GB-hours) | Savings |
|---------------|------------------|----------------------------|---------|
| Regular ACI   | ~$0.0012         | $30-50                     | Baseline |
| Spot ACI      | ~$0.0003         | $5-10                      | 70-80% |

**Configuration:**
```yaml
# In k8s/news-processing-cronjob.yaml
metadata:
  annotations:
    virtual-kubelet.io/sku-name: "Standard"
    virtual-kubelet.io/burst-priority: "spot"
```

**When to Use Spot:**
- ✅ Batch jobs (like news processing)
- ✅ Stateless workloads
- ✅ Jobs that can retry on failure
- ✅ Non-urgent processing
- ✅ Cost is a priority

**When to Use Regular:**
- ❌ Time-sensitive processing
- ❌ Cannot tolerate interruptions
- ❌ Jobs that cannot retry
- ❌ High-priority workloads

**Recommendation for Your Use Case:**
✅ **Use Spot Instances** - Your workload is perfect for spot:
- Runs on schedule (not urgent)
- Can retry (backoffLimit: 2)
- Stateless (no data loss on eviction)
- Significant cost savings

---

## 2. Resource Allocation Strategies

### Current Configuration (Optimized)

```yaml
resources:
  requests:
    memory: "3Gi"  # Guaranteed allocation
    cpu: "1000m"   # 1 vCPU
  limits:
    memory: "5Gi"  # Max allowed
    cpu: "2000m"   # 2 vCPUs
```

### Alternative Configurations

#### A. Conservative (Higher Reliability)

Best for: First deployment, uncertain workload characteristics

```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "1500m"
  limits:
    memory: "6Gi"
    cpu: "2500m"
```

**Pros:**
- Less likely to OOM (out of memory)
- More headroom for unexpected spikes
- Better performance

**Cons:**
- Higher cost (~$12-15/month)
- May waste resources

#### B. Aggressive (Lower Cost)

Best for: Optimized workload, tight budget

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "1500m"
```

**Pros:**
- Lower cost (~$3-5/month)
- Minimal resource waste

**Cons:**
- Higher risk of OOM
- Slower processing
- May need more retries

#### C. Burstable (Recommended for Variable Workload)

Best for: Variable article counts, unpredictable load

```yaml
resources:
  requests:
    memory: "2Gi"   # Low baseline
    cpu: "500m"
  limits:
    memory: "5Gi"   # High ceiling
    cpu: "2000m"
```

**Pros:**
- Pay for baseline (2GB) most of the time
- Can burst to 5GB when needed
- Cost-effective for variable workloads

**Cons:**
- More complex to monitor
- Performance variability

**How It Works:**
- You pay for `requests` continuously
- Can use up to `limits` when available
- Billed for actual usage above requests

---

## 3. Retry and Failure Policies

### Current Configuration

```yaml
spec:
  backoffLimit: 2  # Retry up to 2 times
  activeDeadlineSeconds: 14400  # 4 hour timeout
```

### Alternative Configurations

#### A. Aggressive Retry (High Reliability)

Best for: Critical jobs, high spot eviction rate

```yaml
spec:
  backoffLimit: 5  # Retry up to 5 times
  activeDeadlineSeconds: 18000  # 5 hour timeout
```

**Exponential Backoff:**
- Attempt 1: Immediate
- Attempt 2: ~10 seconds later
- Attempt 3: ~20 seconds later
- Attempt 4: ~40 seconds later
- Attempt 5: ~80 seconds later

**Use Case:**
- High spot eviction rate in your region
- Critical to complete processing
- Can tolerate longer total time

#### B. No Retry (Manual Investigation)

Best for: Debugging, development

```yaml
spec:
  backoffLimit: 0  # No automatic retries
  activeDeadlineSeconds: 14400
```

**Use Case:**
- Investigating failures
- Development/testing
- Want to inspect failed state

#### C. Long Running with Checkpointing (Advanced)

Best for: Very long jobs (>4 hours)

```yaml
spec:
  backoffLimit: 3
  activeDeadlineSeconds: 28800  # 8 hours
```

**Requires:**
- Implement checkpointing in job code
- Save progress periodically
- Resume from last checkpoint on retry

**Example Checkpointing:**
```python
# In news_processing_job.py
import pickle

CHECKPOINT_FILE = '/app/data/checkpoint.pkl'

def save_checkpoint(processed_articles):
    with open(CHECKPOINT_FILE, 'wb') as f:
        pickle.dump(processed_articles, f)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'rb') as f:
            return pickle.load(f)
    return []

# In main processing loop
processed = load_checkpoint()
for article in articles:
    if article.url not in processed:
        process_article(article)
        processed.append(article.url)
        save_checkpoint(processed)
```

---

## 4. Scheduling Configurations

### Current Schedule

```yaml
schedule: "0 2 */2 * *"  # Every 2 days at 2 AM UTC
```

### Alternative Schedules

#### A. Cost-Optimized (Less Frequent)

**Every 3 Days:**
```yaml
schedule: "0 2 */3 * *"  # Every 3 days at 2 AM UTC
```

**Monthly Cost:** $3-7 (vs $5-10)
**Trade-off:** Less frequent data updates

**Weekly:**
```yaml
schedule: "0 2 * * 0"  # Every Sunday at 2 AM UTC
```

**Monthly Cost:** $1-2
**Trade-off:** Significant delay in data freshness

#### B. High Frequency (More Current Data)

**Daily:**
```yaml
schedule: "0 2 * * *"  # Every day at 2 AM UTC
```

**Monthly Cost:** $15-30
**Benefit:** Always-fresh data

**Twice Daily:**
```yaml
schedule: "0 2,14 * * *"  # 2 AM and 2 PM UTC daily
```

**Monthly Cost:** $30-60
**Benefit:** Near real-time data

#### C. Business Hours Only

**Weekdays Only:**
```yaml
schedule: "0 2 * * 1-5"  # Monday-Friday at 2 AM UTC
```

**Monthly Cost:** $7-14 (vs $5-10)
**Benefit:** Skip weekends when markets are closed

#### D. Timezone-Aware

**Singapore Time (UTC+8):**
```yaml
# 2 AM Singapore = 6 PM UTC (previous day)
schedule: "0 18 */2 * *"
```

Or use timezone annotation (if supported):
```yaml
spec:
  timeZone: "Asia/Singapore"
  schedule: "0 2 */2 * *"
```

---

## 5. Advanced ACI Configurations

### A. GPU Instances (For Heavy ML)

If you need GPU acceleration (e.g., for large transformer models):

```yaml
metadata:
  annotations:
    virtual-kubelet.io/sku-name: "Standard"
    virtual-kubelet.io/gpu-type: "K80"  # or V100, P100
    virtual-kubelet.io/gpu-count: "1"

resources:
  limits:
    nvidia.com/gpu: 1
```

**Cost:** ~$0.50-2.00/hour (expensive!)
**Use Case:**
- Training models
- Very large inference (GPT-3 size models)
- Real-time video processing

**Recommendation:** ❌ Not needed for your workload
- FinBERT runs fine on CPU
- spaCy doesn't benefit from GPU
- Cost outweighs benefit

### B. Persistent Volumes

For caching models between runs:

```yaml
volumeMounts:
- name: model-cache
  mountPath: /app/models

volumes:
- name: model-cache
  azureFile:
    secretName: azure-file-secret
    shareName: model-cache
    readOnly: false
```

**Benefits:**
- Faster startup (no re-download)
- Consistent model versions
- Reduced bandwidth

**Cost:** ~$0.06/GB/month (Azure Files)
**Setup Required:**
```bash
# Create storage account and file share
az storage account create --name sentifinancesstorage --sku Standard_LRS
az storage share create --name model-cache --account-name sentifinancesstorage
```

**Recommendation:** ✅ Consider for future optimization
- Would save ~2-3 minutes startup time
- Models are ~1.5GB total
- Cost: ~$0.10/month

### C. Private Networking

For secure database access:

```yaml
metadata:
  annotations:
    virtual-kubelet.io/subnet-name: "aci-subnet"
    virtual-kubelet.io/vnet-name: "sentifinance-vnet"
```

**Use Case:**
- Database with private endpoint
- Compliance requirements
- Enhanced security

**Setup Required:**
```bash
# Create virtual network integration
az network vnet create --name sentifinance-vnet --resource-group sentifinance-rg
az network vnet subnet create --name aci-subnet --vnet-name sentifinance-vnet
```

**Recommendation:** ⚠️ Optional (your DB may already be public)
- Check if database allows public access
- If yes, this adds complexity without benefit
- If no, implement this for connectivity

### D. Environment Variable from Azure Key Vault

For ultra-secure secrets:

```yaml
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: azure-keyvault-secret
      key: openai-api-key
```

With virtual-kubelet integration:
```yaml
metadata:
  annotations:
    virtual-kubelet.io/key-vault-secret-uri: "https://sentifiancevault.vault.azure.net/secrets/openai-key"
```

**Benefits:**
- Centralized secret management
- Audit logs for secret access
- Automatic rotation

**Setup Required:**
```bash
# Create Key Vault
az keyvault create --name sentifinancevault --resource-group sentifinance-rg

# Add secrets
az keyvault secret set --vault-name sentifinancevault --name openai-key --value "sk-..."
```

**Recommendation:** 🔒 Optional but recommended for production
- Better security than K8s secrets
- Centralized secret management
- Minimal added complexity

---

## 6. Monitoring and Diagnostics

### A. Container Insights (Azure Monitor)

Enable detailed monitoring:

```yaml
metadata:
  annotations:
    virtual-kubelet.io/log-analytics-workspace-id: "<WORKSPACE_ID>"
    virtual-kubelet.io/log-analytics-workspace-key: "<WORKSPACE_KEY>"
```

**What You Get:**
- Real-time logs
- Performance metrics (CPU, memory)
- Diagnostics
- Alerts

**Cost:** ~$2.30/GB ingested
**Typical Usage:** ~0.5-1GB/month for batch jobs
**Total Cost:** ~$1-3/month

**Setup:**
```bash
# Run the monitoring setup script
./scripts/setup-monitoring.sh
```

### B. Application Insights

For application-level monitoring:

```yaml
env:
- name: APPINSIGHTS_INSTRUMENTATIONKEY
  value: "<instrumentation-key>"
```

Add to Python code:
```python
from applicationinsights import TelemetryClient
tc = TelemetryClient('<instrumentation-key>')

tc.track_event('NewsProcessingStarted')
tc.track_metric('ArticlesProcessed', article_count)
tc.track_exception()  # Auto-captures exceptions
```

**Benefits:**
- Custom metrics
- Distributed tracing
- Exception tracking
- Performance profiling

**Cost:** Free tier: 5GB/month, then $2.30/GB

---

## 7. Cost Optimization Strategies

### Strategy 1: Dynamic Scheduling

Adjust frequency based on market activity:

```python
# In a scheduler script
import datetime

def get_cron_schedule():
    # More frequent during market hours, less on weekends
    if datetime.today().weekday() < 5:  # Weekday
        return "0 2,14 * * 1-5"  # Twice daily
    else:  # Weekend
        return "0 2 * * 0"  # Once weekly
```

### Strategy 2: Article Count Throttling

Limit processing for cost control:

```yaml
env:
- name: MAX_ARTICLES
  value: "50"  # Process max 50 articles per run
```

**Effect:**
- Faster execution (1-2 hours instead of 3-4)
- Lower resource usage
- Reduced cost (~50%)

**Trade-off:** May miss some articles

### Strategy 3: Burstable Resources

Start small, scale up if needed:

```yaml
resources:
  requests:
    memory: "1Gi"   # Low initial request
  limits:
    memory: "5Gi"   # High ceiling
```

**How It Works:**
- Pay for 1GB baseline
- Can burst to 5GB if needed
- Only pay for actual usage

**Best For:** Variable workloads

### Strategy 4: Preemptible Instances with Fallback

Try spot first, fallback to regular if evicted:

```yaml
# Job 1: Spot instance
annotations:
  virtual-kubelet.io/burst-priority: "spot"

# Job 2: Regular instance (only if Job 1 fails)
# Implemented via CronJob failure handling
```

Requires custom logic in CronJob controller.

### Strategy 5: Shared Model Cache

Cache models across runs:

```python
# Download models once, reuse
if not os.path.exists('/app/models/spacy'):
    spacy.cli.download('en_core_web_trf')
```

With persistent volume, this saves:
- ~2-3 min download time
- ~500MB bandwidth per run
- Small storage cost ($0.10/month)

---

## 8. Recommended Configuration Matrix

### Development

```yaml
# k8s/news-processing-cronjob.yaml
spec:
  schedule: "0 */6 * * *"  # Every 6 hours (testing)
  backoffLimit: 0  # No retry (easier debugging)

resources:
  requests:
    memory: "2Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "1500m"

env:
- name: MAX_ARTICLES
  value: "10"  # Small batch for testing
- name: LOG_LEVEL
  value: "DEBUG"
```

**Cost:** ~$15-20/month

### Staging

```yaml
spec:
  schedule: "0 2 * * *"  # Daily
  backoffLimit: 1  # Single retry

resources:
  requests:
    memory: "3Gi"
    cpu: "1000m"
  limits:
    memory: "5Gi"
    cpu: "2000m"

env:
- name: MAX_ARTICLES
  value: "50"  # Medium batch
- name: LOG_LEVEL
  value: "INFO"

metadata:
  annotations:
    virtual-kubelet.io/burst-priority: "regular"  # Reliable instances
```

**Cost:** ~$20-30/month

### Production (Current Recommended)

```yaml
spec:
  schedule: "0 2 */2 * *"  # Every 2 days
  backoffLimit: 2  # 2 retries

resources:
  requests:
    memory: "3Gi"
    cpu: "1000m"
  limits:
    memory: "5Gi"
    cpu: "2000m"

env:
- name: LOG_LEVEL
  value: "INFO"

metadata:
  annotations:
    virtual-kubelet.io/burst-priority: "spot"  # Cost optimized
    virtual-kubelet.io/log-analytics-workspace-id: "<ID>"
    virtual-kubelet.io/log-analytics-workspace-key: "<KEY>"
```

**Cost:** ~$5-10/month + $1-3 monitoring = **$6-13/month total**

### Production (High Reliability)

```yaml
spec:
  schedule: "0 2 * * *"  # Daily
  backoffLimit: 3  # 3 retries

resources:
  requests:
    memory: "4Gi"
    cpu: "1500m"
  limits:
    memory: "6Gi"
    cpu: "2500m"

metadata:
  annotations:
    virtual-kubelet.io/burst-priority: "regular"  # No spot evictions
```

**Cost:** ~$40-50/month (no spot savings)

---

## 9. Troubleshooting Common Issues

### Issue 1: Spot Instance Evictions

**Symptoms:**
- Job fails with "Container evicted"
- Happens during peak hours

**Solutions:**
1. Increase retry limit:
   ```yaml
   backoffLimit: 3  # More retries
   ```

2. Switch to regular instances:
   ```yaml
   annotations:
     virtual-kubelet.io/burst-priority: "regular"
   ```

3. Schedule during off-peak:
   ```yaml
   schedule: "0 2 * * *"  # 2 AM has lower eviction rate
   ```

### Issue 2: Out of Memory (OOM)

**Symptoms:**
- Pod killed with exit code 137
- Logs show memory errors

**Solutions:**
1. Increase memory limit:
   ```yaml
   resources:
     limits:
       memory: "6Gi"  # Increase from 5Gi
   ```

2. Reduce batch size:
   ```yaml
   env:
   - name: MAX_ARTICLES
     value: "50"  # Process fewer articles
   ```

3. Optimize code:
   ```python
   # Clear memory after processing each article
   import gc
   gc.collect()
   ```

### Issue 3: Timeout

**Symptoms:**
- Job fails after 4 hours
- Logs show incomplete processing

**Solutions:**
1. Increase deadline:
   ```yaml
   activeDeadlineSeconds: 18000  # 5 hours
   ```

2. Optimize processing:
   - Parallel processing
   - Faster models
   - Better database queries

3. Increase resources:
   ```yaml
   resources:
     limits:
       cpu: "3000m"  # 3 vCPUs
   ```

---

## 10. Final Recommendations

### For Your Workload (News Processing Batch Job)

✅ **Recommended Configuration:**

```yaml
# Spot instances for cost savings
virtual-kubelet.io/burst-priority: "spot"

# Optimized resources
resources:
  requests:
    memory: "3Gi"
    cpu: "1000m"
  limits:
    memory: "5Gi"
    cpu: "2000m"

# Retry for reliability
backoffLimit: 2

# Current schedule is good
schedule: "0 2 */2 * *"

# Enable monitoring
virtual-kubelet.io/log-analytics-workspace-id: "<ID>"
```

**Expected Outcome:**
- Cost: $6-13/month (total)
- Reliability: 95%+ (with retries)
- Performance: 2-4 hours per run
- Data freshness: Every 2 days

### When to Re-evaluate

**Increase frequency if:**
- Need more current data
- Market volatility increases
- User demand for real-time data

**Decrease frequency if:**
- Data doesn't change much
- Cost becomes concern
- Processing takes too long

**Switch to regular instances if:**
- Spot eviction rate >20%
- Critical data processing
- SLA requirements

---

## Summary

Your current configuration is **well-optimized** for your use case:
- ✅ Spot instances (70% cost savings)
- ✅ Right-sized resources (3-5Gi)
- ✅ Appropriate retry policy
- ✅ Good schedule (every 2 days)

**Total Monthly Cost:** $6-13 (vs $200+ for always-running monolith)

**No changes needed immediately** - deploy and monitor!
