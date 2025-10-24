# AKS Deployment Troubleshooting Guide

## Current Issue

**Symptom**: Deployment times out with "timed out waiting for the condition"

```
Waiting for deployment "sentifinance-backend" rollout to finish:
1 out of 3 new replicas have been updated...
error: timed out waiting for the condition
```

This means the new pods are failing to become "Ready" within the 5-minute timeout.

---

## Quick Diagnosis

### Run the Diagnostic Script

```bash
# First, connect to your AKS cluster
az aks get-credentials --resource-group <your-rg> --name <your-cluster> --overwrite-existing

# Then run the diagnostic
./scripts/diagnose-aks-deployment.sh
```

### Manual Quick Check

```bash
# 1. Check pod status
kubectl get pods -n sentifinance

# 2. Check recent events
kubectl get events -n sentifinance --sort-by='.lastTimestamp' | tail -20

# 3. Get logs from failing pod
kubectl logs -n sentifinance <pod-name>

# 4. Describe failing pod
kubectl describe pod -n sentifinance <pod-name>
```

---

## Common Causes & Solutions

### 1. Application Import Errors (Most Likely Given Recent Changes)

**Symptoms:**
- Pods show `CrashLoopBackOff`
- Logs show `ModuleNotFoundError` or `ImportError`
- Example: `ModuleNotFoundError: No module named 'crawl4ai'`

**Diagnosis:**
```bash
kubectl logs -n sentifinance <pod-name> | grep -i "error\|import"
```

**Cause:**
- App tries to import `crawl4ai`, `transformers`, or `shap` which aren't installed
- Our recent changes made imports lazy, but Flask might still import services on startup

**Solution:**

The lazy loading we just implemented should fix this, but if it's still failing:

1. **Check if the new image was built:**
   ```bash
   kubectl get deployment sentifinance-backend -n sentifinance -o jsonpath='{.spec.template.spec.containers[0].image}'
   ```
   Should show a recent commit hash, not just `:latest`

2. **Force a rollout restart:**
   ```bash
   kubectl rollout restart deployment/sentifinance-backend -n sentifinance
   ```

3. **If still failing, check what's being imported:**
   ```bash
   # Get logs from the failing pod
   kubectl logs -n sentifinance $(kubectl get pods -n sentifinance -l app=sentifinance-backend -o jsonpath='{.items[0].metadata.name}') --tail=100
   ```

---

### 2. Image Pull Errors

**Symptoms:**
- Pods stuck in `ImagePullBackOff` or `ErrImagePull`
- Event log shows "Failed to pull image"

**Diagnosis:**
```bash
kubectl describe pod -n sentifinance <pod-name> | grep -A 10 "Events:"
```

**Causes:**
- ACR credentials expired or incorrect
- Image doesn't exist in registry
- Network issues

**Solutions:**

1. **Check if image exists in ACR:**
   ```bash
   az acr repository show-tags \
     --name sentifinancetwo \
     --repository sentifinance-backend \
     --orderby time_desc \
     --output table | head -10
   ```

2. **Recreate ACR secret:**
   ```bash
   # Get ACR credentials
   ACR_SERVER="sentifinancetwo.azurecr.io"
   ACR_USERNAME=$(az acr credential show --name sentifinancetwo --query username -o tsv)
   ACR_PASSWORD=$(az acr credential show --name sentifinancetwo --query passwords[0].value -o tsv)

   # Delete old secret
   kubectl delete secret acr-secret -n sentifinance --ignore-not-found

   # Create new secret
   kubectl create secret docker-registry acr-secret \
     --docker-server=$ACR_SERVER \
     --docker-username=$ACR_USERNAME \
     --docker-password=$ACR_PASSWORD \
     --namespace=sentifinance

   # Restart deployment
   kubectl rollout restart deployment/sentifinance-backend -n sentifinance
   ```

---

### 3. Out of Memory (OOMKilled)

**Symptoms:**
- Pods show `OOMKilled` status
- Exit code 137

**Diagnosis:**
```bash
kubectl describe pod -n sentifinance <pod-name> | grep -i "oom\|137"
```

**Solution:**

Increase memory limits in [k8s/deployment.yaml](k8s/deployment.yaml):

```yaml
resources:
  requests:
    memory: "512Mi"  # Increase from 256Mi
  limits:
    memory: "2Gi"    # Increase from 1536Mi
```

**Note:** This is unlikely now since we removed heavy dependencies (spacy, torch, etc.)

---

### 4. Readiness Probe Failures

**Symptoms:**
- Pods stay in `Running` but not `Ready` (0/1 Ready)
- Events show "Readiness probe failed"

**Diagnosis:**
```bash
kubectl describe pod -n sentifinance <pod-name> | grep -A 5 "Readiness:"
kubectl logs -n sentifinance <pod-name> | tail -50
```

**Causes:**
- App takes longer than 30 seconds to start
- Health endpoint `/` not responding
- Database connection failing

**Solutions:**

1. **Increase readiness probe delay** in [k8s/deployment.yaml](k8s/deployment.yaml):
   ```yaml
   readinessProbe:
     httpGet:
       path: /
       port: 5001
     initialDelaySeconds: 60  # Increase from 30
     periodSeconds: 10
   ```

2. **Check if database is accessible:**
   ```bash
   # Exec into pod
   kubectl exec -it -n sentifinance <pod-name> -- bash

   # Test database connection (inside pod)
   python -c "
   import os
   from sqlalchemy import create_engine
   engine = create_engine(os.getenv('DATABASE_URI'))
   engine.connect()
   print('Database connection successful!')
   "
   ```

---

### 5. Missing Environment Variables / Secrets

**Symptoms:**
- Pods crash with KeyError or environment variable errors
- Logs show "SECRET_KEY not set" or similar

**Diagnosis:**
```bash
kubectl logs -n sentifinance <pod-name> | grep -i "KeyError\|not set\|environment"
```

**Solution:**

Check if secrets exist:
```bash
kubectl get secret sentifinance-secrets -n sentifinance
```

If missing, they should be created by the CD workflow. Check the workflow logs:
```bash
gh run view --log | grep -A 20 "Create Kubernetes secrets"
```

---

### 6. Node Resource Constraints

**Symptoms:**
- Pods stuck in `Pending` status
- Events show "Insufficient cpu" or "Insufficient memory"

**Diagnosis:**
```bash
kubectl describe pod -n sentifinance <pod-name> | grep -i "insufficient"
kubectl top nodes
```

**Solution:**

1. **Reduce resource requests temporarily:**
   ```yaml
   resources:
     requests:
       memory: "128Mi"  # Reduce
       cpu: "50m"       # Reduce
   ```

2. **Or scale down replica count:**
   ```yaml
   spec:
     replicas: 1  # Reduce from 3
   ```

---

## Most Likely Issue for Your Current Situation

Based on the recent changes (removing spacy, crawl4ai, transformers), the most likely issue is:

### **Import Errors During Flask App Initialization**

Even though we made the imports lazy, if the app still tries to import the service modules during initialization, it will fail.

### **How to Verify:**

1. **Check the latest pod logs:**
   ```bash
   # Get the failing pod name
   POD=$(kubectl get pods -n sentifinance -l app=sentifinance-backend --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

   # Get logs
   kubectl logs -n sentifinance $POD
   ```

2. **Look for:**
   - `ModuleNotFoundError: No module named 'crawl4ai'`
   - `ModuleNotFoundError: No module named 'transformers'`
   - `ModuleNotFoundError: No module named 'shap'`
   - Any other import errors

### **If You See Import Errors:**

The issue is that our lazy loading isn't working, or something is still importing these modules eagerly.

**Quick Fix Options:**

**Option A: Temporarily add dependencies back to backend**
```bash
# In Backend/pyproject.toml, add minimal versions
dependencies = [
    # ... existing deps ...
    "transformers>=4.35.0",  # Add back temporarily
    "torch>=2.1.0",          # Add back temporarily
]
```
Then redeploy.

**Option B: Make services truly optional**
Create a try/except wrapper in `app/services/__init__.py`:
```python
try:
    from .sentiment_analysis import SentimentAnalyzer
except ImportError:
    SentimentAnalyzer = None  # Will be None if deps not available

try:
    from .article_scraper import scrape_article
except ImportError:
    scrape_article = None  # Will be None if deps not available
```

**Option C: Don't import these services at app startup**
Comment out unused imports in route files.

---

## Step-by-Step Recovery Process

1. **Diagnose the exact issue:**
   ```bash
   ./scripts/diagnose-aks-deployment.sh > diagnosis.txt
   cat diagnosis.txt
   ```

2. **Based on diagnosis, apply fix** (see solutions above)

3. **Commit and push fix:**
   ```bash
   git add .
   git commit -m "fix: resolve deployment issue"
   git push origin dev
   ```

4. **Monitor deployment:**
   ```bash
   # Watch in real-time
   kubectl get pods -n sentifinance -w
   ```

5. **If still failing, rollback to previous version:**
   ```bash
   # Find previous working image
   az acr repository show-tags --name sentifinancetwo --repository sentifinance-backend --orderby time_desc -o table

   # Update to specific tag
   kubectl set image deployment/sentifinance-backend \
     sentifinance-backend=sentifinancetwo.azurecr.io/sentifinance-backend:<previous-working-tag> \
     -n sentifinance
   ```

---

## Prevention for Future

1. **Test locally before pushing:**
   ```bash
   cd Backend
   docker build -t backend-test .
   docker run --rm -e DATABASE_URI=sqlite:///test.db backend-test python -c "from app import create_app; create_app()"
   ```

2. **Add startup health check to Dockerfile:**
   ```dockerfile
   # Test app can start
   RUN python -c "from app import create_app; create_app(); print('App starts OK')"
   ```

3. **Use staging environment:**
   - Deploy to staging namespace first
   - Test thoroughly
   - Then promote to production

---

## Quick Reference Commands

```bash
# Get cluster credentials
az aks get-credentials --resource-group <rg> --name <cluster> --overwrite-existing

# Watch pods
kubectl get pods -n sentifinance -w

# Get logs (follow)
kubectl logs -f -n sentifinance <pod-name>

# Describe pod (see events)
kubectl describe pod -n sentifinance <pod-name>

# Exec into pod
kubectl exec -it -n sentifinance <pod-name> -- bash

# Restart deployment
kubectl rollout restart deployment/sentifinance-backend -n sentifinance

# Check rollout status
kubectl rollout status deployment/sentifinance-backend -n sentifinance

# Rollback deployment
kubectl rollout undo deployment/sentifinance-backend -n sentifinance

# Scale deployment
kubectl scale deployment/sentifinance-backend --replicas=1 -n sentifinance

# Delete pod (will recreate)
kubectl delete pod <pod-name> -n sentifinance

# View recent events
kubectl get events -n sentifinance --sort-by='.lastTimestamp' | tail -30
```

---

## Contact for Help

If you're still stuck after trying the above:

1. Run the diagnostic script and save output:
   ```bash
   ./scripts/diagnose-aks-deployment.sh > diagnosis.txt
   ```

2. Get pod logs:
   ```bash
   kubectl logs -n sentifinance <failing-pod> > pod-logs.txt
   ```

3. Get pod description:
   ```bash
   kubectl describe pod -n sentifinance <failing-pod> > pod-describe.txt
   ```

4. Share these files for further analysis

---

## Summary

**Most likely issue**: Import errors due to missing dependencies (crawl4ai, transformers, shap)

**Quick diagnosis**: Run `./scripts/diagnose-aks-deployment.sh`

**Quick fix**: Check pod logs, identify the import error, apply lazy loading or make service optional

**Nuclear option**: Rollback to `before-microservices-refactor` tag if nothing works
