# SentiFinance Troubleshooting Guide

This guide helps you diagnose and fix common issues in the SentiFinance application across all components: Frontend, Backend, Database, Kubernetes, and CI/CD.

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Log Locations](#log-locations)
3. [Common Errors by Component](#common-errors-by-component)
   - [Kubernetes & Deployment](#1-kubernetes--deployment-errors)
   - [Database](#2-database-errors)
   - [Backend API](#3-backend-api-errors)
   - [Frontend](#4-frontend-errors)
   - [CI/CD Pipeline](#5-cicd-pipeline-errors)
   - [News Processing Job](#6-news-processing-job-errors)
   - [Azure Infrastructure](#7-azure-infrastructure-errors)
4. [Debugging Tools & Commands](#debugging-tools--commands)
5. [Performance Issues](#performance-issues)
6. [Getting Help](#getting-help)

---

## Quick Diagnostics

Start here for a high-level health check:

```bash
# 1. Check if pods are running
kubectl get pods -n sentifinance

# 2. Check if service has external IP
kubectl get service sentifinance-service -n sentifinance

# 3. Check recent pod logs
kubectl logs -n sentifinance -l app=sentifinance-backend --tail=50

# 4. Check database connectivity
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app; app=create_app(); print('DB OK')"

# 5. Check recent CI/CD runs
gh run list --limit 5

# 6. Test API endpoint (replace with your external IP)
SERVICE_IP=$(kubectl get service sentifinance-service -n sentifinance -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -I http://$SERVICE_IP/api/health
```

---

## Log Locations

### Local Development Logs

| Component | Location | Format |
|-----------|----------|--------|
| Backend API | `Backend/data_ingestion_gnews.log` | Plain text |
| Flask logs | Console output (stdout) | Structured logging |
| Frontend (dev) | Browser console + terminal | JavaScript console |
| Database migrations | Console output | Flask-Migrate output |

### Kubernetes Logs

```bash
# Main backend application logs
kubectl logs -n sentifinance deployment/sentifinance-backend --tail=100 -f

# Specific pod logs
kubectl logs -n sentifinance <pod-name> --tail=100 -f

# Previous crashed pod logs
kubectl logs -n sentifinance <pod-name> --previous

# All pods with label
kubectl logs -n sentifinance -l app=sentifinance-backend --tail=50

# News processing CronJob logs
kubectl logs -n sentifinance -l job-name=news-processing-job --tail=200

# Database migration job logs
kubectl logs -n sentifinance -l job-name=db-migration-job --tail=100
```

### Azure Logs

```bash
# AKS cluster logs via Azure CLI
az aks get-credentials --resource-group sentifinance2 --name sentifinance-aks
kubectl logs -n kube-system -l component=kubelet

# Container instance logs
az container logs --resource-group sentifinance2 --name <container-name>

# Azure Monitor / Application Insights
# Access via Azure Portal → Application Insights → Logs
```

### CI/CD Logs

```bash
# GitHub Actions logs via CLI
gh run list
gh run view <run-id> --log

# View specific job
gh run view <run-id> --log --job <job-id>

# Download logs
gh run download <run-id>
```

---

## Common Errors by Component

## 1. Kubernetes & Deployment Errors

### Error: `ImagePullBackOff` or `ErrImagePull`

**Symptom:**
```bash
kubectl get pods -n sentifinance
# NAME                                   READY   STATUS             RESTARTS   AGE
# sentifinance-backend-xxx               0/1     ImagePullBackOff   0          2m
```

**Cause:** AKS cannot pull the Docker image from ACR

**Diagnosis:**
```bash
# Check pod events
kubectl describe pod -n sentifinance <pod-name>

# Look for errors like:
# Failed to pull image "sentifinancetwo.azurecr.io/sentifinance-backend:latest":
# rpc error: code = Unknown desc = failed to pull and unpack image
```

**Fix:**

```bash
# 1. Verify ACR is attached to AKS
az aks show --resource-group sentifinance2 --name sentifinance-aks \
  --query "servicePrincipalProfile"

# 2. Manually attach ACR if needed
az aks update --resource-group sentifinance2 \
  --name sentifinance-aks \
  --attach-acr sentifinancetwo

# 3. Check image exists in ACR
az acr repository show-tags \
  --name sentifinancetwo \
  --repository sentifinance-backend \
  --orderby time_desc \
  --output table

# 4. Force pod restart to retry pull
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

**Reference:** k8s/README.md:110-119

---

### Error: `CrashLoopBackOff`

**Symptom:**
```bash
kubectl get pods -n sentifinance
# NAME                                   READY   STATUS             RESTARTS   AGE
# sentifinance-backend-xxx               0/1     CrashLoopBackOff   5          10m
```

**Cause:** Application crashes immediately after starting

**Diagnosis:**
```bash
# Check pod logs
kubectl logs -n sentifinance <pod-name> --tail=100

# Check previous crashed container logs
kubectl logs -n sentifinance <pod-name> --previous

# Common error messages to look for:
# - "connection to server was refused" → Database connectivity issue
# - "ModuleNotFoundError" → Missing Python dependency
# - "secret not found" → Missing Kubernetes secret
# - "OOMKilled" → Out of memory (see below)
```

**Common Fixes:**

**A. Database Connection Issue**
```bash
# Verify DATABASE_URI secret exists
kubectl get secret -n sentifinance sentifinance-secrets -o yaml

# Check if External Secrets Operator synced from Key Vault
kubectl get externalsecret -n sentifinance
kubectl describe externalsecret -n sentifinance sentifinance-external-secrets

# Manually verify database connectivity
kubectl run -n sentifinance -it --rm debug --image=postgres:12 --restart=Never -- \
  psql "<DATABASE_URI_VALUE>"
```

**B. Missing Dependencies**
```bash
# Rebuild Docker image with all dependencies
cd Backend
docker build -t sentifinancetwo.azurecr.io/sentifinance-backend:latest .
docker push sentifinancetwo.azurecr.io/sentifinance-backend:latest

# Force update deployment
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

**C. Missing Secrets**
```bash
# List all secrets
kubectl get secrets -n sentifinance

# Verify required secrets exist
kubectl get secret sentifinance-secrets -n sentifinance -o jsonpath='{.data}' | jq 'keys'

# Should include: database-uri, jwt-secret-key, secret-key, gemini-api-key, openai-api-key

# If missing, sync from Key Vault
kubectl delete externalsecret -n sentifinance sentifinance-external-secrets
kubectl apply -f k8s/external-secrets.yaml
```

**Reference:** RECREATION_GUIDE.md (search for "CrashLoopBackOff")

---

### Error: `OOMKilled` (Out of Memory)

**Symptom:**
```bash
kubectl describe pod -n sentifinance <pod-name>
# State:          Terminated
# Reason:         OOMKilled
# Exit Code:      137
```

**Cause:** Pod exceeded memory limits (common with FinBERT model loading)

**Diagnosis:**
```bash
# Check current memory limits
kubectl get deployment -n sentifinance sentifinance-backend -o yaml | grep -A5 resources

# Check actual memory usage
kubectl top pods -n sentifinance
```

**Fix:**

**Option 1: Verify Lazy Loading (Recommended)**
```bash
# Check if lazy loading is enabled in sentiment_analysis.py
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  grep -n "@property" /app/app/services/sentiment_analysis.py

# Should show @property decorators before finbert_pipeline and meta_classifier

# If missing, ensure you're deploying from dev branch
# See WORKFLOW_DEV_BRANCH_CONFIG.md
```

**Option 2: Increase Memory Limits**
```yaml
# Edit k8s/deployment.yaml
resources:
  requests:
    memory: "1Gi"      # Increase from 512Mi
    cpu: "500m"
  limits:
    memory: "2Gi"      # Increase from 1Gi
    cpu: "1000m"

# Apply changes
kubectl apply -f k8s/deployment.yaml
```

**Option 3: Verify News Processor is Separate**
```bash
# Main backend should NOT have heavy ML libs
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  pip list | grep transformers

# Should show: (no output or lightweight version)

# News processor SHOULD have heavy libs
kubectl logs -n sentifinance -l job-name=news-processing-job | head -20
# Should show: "Loading FinBERT model..."
```

**Reference:** WORKFLOW_DEV_BRANCH_CONFIG.md:252-262, Backend/Dockerfile

---

### Error: Pod stuck in `Pending` state

**Symptom:**
```bash
kubectl get pods -n sentifinance
# NAME                                   READY   STATUS    RESTARTS   AGE
# sentifinance-backend-xxx               0/1     Pending   0          5m
```

**Cause:** No available nodes, insufficient resources, or PVC issues

**Diagnosis:**
```bash
kubectl describe pod -n sentifinance <pod-name>

# Look for messages like:
# - "0/4 nodes are available: 4 Insufficient memory"
# - "FailedScheduling: no nodes available to schedule pods"
# - "persistentvolumeclaim not found"
```

**Fix:**
```bash
# Check node resources
kubectl top nodes
kubectl describe nodes

# Scale up AKS cluster if needed
az aks scale --resource-group sentifinance2 \
  --name sentifinance-aks \
  --node-count 4

# Check pod resource requests
kubectl get deployment -n sentifinance sentifinance-backend -o yaml | grep -A10 resources
```

---

### Error: `Service has no External IP`

**Symptom:**
```bash
kubectl get service -n sentifinance sentifinance-service
# NAME                   TYPE           EXTERNAL-IP   PORT(S)
# sentifinance-service   LoadBalancer   <pending>     80:30080/TCP
```

**Cause:** LoadBalancer provisioning takes time or failed

**Diagnosis:**
```bash
# Wait 2-5 minutes, then check again
kubectl get service -n sentifinance sentifinance-service -w

# Check service events
kubectl describe service -n sentifinance sentifinance-service

# Check AKS load balancer
az network lb list --resource-group MC_sentifinance2_sentifinance-aks_southeastasia
```

**Fix:**
```bash
# If stuck for >10 minutes, delete and recreate service
kubectl delete service -n sentifinance sentifinance-service
kubectl apply -f k8s/service.yaml

# Verify service type is LoadBalancer
kubectl get service -n sentifinance sentifinance-service -o yaml | grep type
```

**Reference:** RECREATION_GUIDE.md (search for "LoadBalancer")

---

## 2. Database Errors

### Error: `FATAL: password authentication failed for user`

**Symptom:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
FATAL:  password authentication failed for user "sentifinance_admin"
```

**Cause:** Incorrect DATABASE_URI or database credentials

**Diagnosis:**
```bash
# Check current DATABASE_URI (without exposing password)
kubectl get secret -n sentifinance sentifinance-secrets -o jsonpath='{.data.database-uri}' | base64 -d | sed 's/:[^@]*@/:***@/'

# Format should be:
# postgresql://username:password@hostname:5432/database_name?sslmode=require
```

**Fix:**
```bash
# 1. Verify Key Vault has correct DATABASE_URI
az keyvault secret show --vault-name <vault-name> --name DATABASE-URI

# 2. Update Key Vault if wrong
az keyvault secret set \
  --vault-name <vault-name> \
  --name DATABASE-URI \
  --value "postgresql://user:pass@host:5432/dbname?sslmode=require"

# 3. Force External Secrets sync
kubectl delete secret -n sentifinance sentifinance-secrets
kubectl delete externalsecret -n sentifinance sentifinance-external-secrets
kubectl apply -f k8s/external-secrets.yaml

# Wait 30 seconds for sync
sleep 30

# 4. Restart pods to pick up new secret
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

**Reference:** terraform/POSTGRESQL_SETUP.md, terraform/SECRETS_SETUP.md

---

### Error: `Database migration failed`

**Symptom:**
```bash
kubectl logs -n sentifinance -l job-name=db-migration-job
# Error: Can't locate revision identified by 'abc123'
# OR
# Target database is not up to date.
```

**Cause:** Migration job failed before pod deployment

**Diagnosis:**
```bash
# Check migration job status
kubectl get jobs -n sentifinance db-migration-job

# Check job logs
kubectl logs -n sentifinance -l job-name=db-migration-job --tail=100

# Check current database schema version
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  flask db current
```

**Fix:**

**Option 1: Re-run Migration Job**
```bash
# Delete failed job
kubectl delete job -n sentifinance db-migration-job

# Re-apply job
kubectl apply -f k8s/db-migration-job.yaml

# Monitor job
kubectl logs -n sentifinance -l job-name=db-migration-job -f
```

**Option 2: Manual Migration**
```bash
# Connect to a running pod and run migrations manually
kubectl exec -n sentifinance deployment/sentifinance-backend -it -- bash

# Inside pod:
cd /app
.venv/bin/flask db upgrade
exit
```

**Option 3: Reset Migration History (DANGEROUS - only for dev)**
```bash
# WARNING: This will drop all migration history
kubectl exec -n sentifinance deployment/sentifinance-backend -it -- bash

# Inside pod:
cd /app/migrations/versions
rm *.py  # Remove all migration files
exit

# Locally, recreate migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

**Reference:** Backend/migrations/, k8s/db-migration-job.yaml

---

### Error: `relation "table_name" does not exist`

**Symptom:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable)
relation "user" does not exist
```

**Cause:** Database migrations have not been applied

**Diagnosis:**
```bash
# Check if migration job completed
kubectl get jobs -n sentifinance

# Verify tables exist
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app, db; app=create_app(); \
  with app.app_context(): print(db.engine.table_names())"
```

**Fix:**
```bash
# Run migrations manually
kubectl exec -n sentifinance deployment/sentifinance-backend -it -- \
  .venv/bin/flask db upgrade

# Restart pods
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

---

## 3. Backend API Errors

### Error: `500 Internal Server Error`

**Symptom:**
```bash
curl http://<external-ip>/api/news
# {"error": "Internal Server Error"}
```

**Diagnosis:**
```bash
# Check backend logs for stack trace
kubectl logs -n sentifinance -l app=sentifinance-backend --tail=200 | grep -A20 "ERROR"

# Common causes:
# - Unhandled exception in route
# - Database query error
# - Missing environment variable
# - Third-party API timeout (Gemini, OpenAI)
```

**Fix:**

**A. Missing Environment Variable**
```bash
# Check if all required secrets are present
kubectl exec -n sentifinance deployment/sentifinance-backend -- env | grep -E "DATABASE_URI|JWT_SECRET|GEMINI_API_KEY"

# If missing, update External Secrets
kubectl apply -f k8s/external-secrets.yaml
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

**B. Third-Party API Error**
```bash
# Test Gemini API key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Test"}]}]}' \
  "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=<GEMINI_KEY>"

# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer <OPENAI_KEY>"
```

**C. Database Connection Pool Exhausted**
```bash
# Check connection pool settings
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  grep -r "SQLALCHEMY_POOL" /app/app/config.py

# Restart pods to reset connections
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

**Reference:** Backend/app/services/, Backend/app/routes/

---

### Error: `JWT Token Invalid or Expired`

**Symptom:**
```json
{
  "error": "Token has expired",
  "message": "Signature verification failed"
}
```

**Cause:** JWT secret key mismatch or token expiration

**Diagnosis:**
```bash
# Check JWT_SECRET_KEY is consistent
kubectl get secret -n sentifinance sentifinance-secrets -o jsonpath='{.data.jwt-secret-key}' | base64 -d

# Verify token expiration settings
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  grep -r "JWT_ACCESS_TOKEN_EXPIRES" /app/app/config.py
```

**Fix:**
```bash
# User solution: Re-login to get a new token
# Frontend should automatically redirect to login page

# Admin solution: Extend token expiration
# Edit Backend/app/config.py
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Increase from 1 hour

# Rebuild and deploy
```

**Reference:** Backend/app/config.py, Backend/app/routes/auth.py

---

### Error: `ModuleNotFoundError: No module named 'transformers'`

**Symptom:**
```
ModuleNotFoundError: No module named 'transformers'
transformers is not installed. This functionality is only available in the news-processor microservice.
```

**Cause:** Main backend trying to load FinBERT (should be news-processor only)

**Diagnosis:**
```bash
# Check if sentiment analysis is being called in backend
kubectl logs -n sentifinance -l app=sentifinance-backend | grep "Loading FinBERT"

# This should NOT appear in backend logs
```

**Fix:**
```bash
# Ensure you're using lazy loading from dev branch
git checkout dev
git pull origin dev

# Verify lazy loading decorator
grep -n "@property" Backend/app/services/sentiment_analysis.py
# Should show @property above finbert_pipeline

# Rebuild and deploy
docker build -f Backend/Dockerfile -t sentifinancetwo.azurecr.io/sentifinance-backend:latest .
docker push sentifinancetwo.azurecr.io/sentifinance-backend:latest
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

**Reference:** Backend/Dockerfile, Backend/Dockerfile.news-processor, WORKFLOW_DEV_BRANCH_CONFIG.md

---

## 4. Frontend Errors

### Error: `Network Error` or `CORS Error` in Browser Console

**Symptom:**
```
Access to XMLHttpRequest at 'http://x.x.x.x/api/news' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Cause:** Frontend calling wrong API URL or CORS not configured

**Diagnosis:**
```bash
# Check frontend environment variables
cat .env
# Should have REACT_APP_API_BASE_URL=http://<external-ip> or http://localhost:5001

# Check browser network tab
# Look for request URL and status code
```

**Fix:**

**Local Development:**
```bash
# Update .env file
echo "REACT_APP_API_BASE_URL=http://localhost:5001" > .env

# Restart React dev server
npm start
```

**Production:**
```bash
# Frontend is served by Flask backend at port 5001
# No separate CORS needed - same origin

# Get external IP
kubectl get service -n sentifinance sentifinance-service

# Update .env.production (if separate build)
REACT_APP_API_BASE_URL=http://<external-ip>

# Rebuild frontend
npm run build

# Copy to backend
cp -r build/* Backend/app/static/
```

**Reference:** .env.example, Backend/app/config.py (CORS settings)

---

### Error: `White screen` or `Blank page` in production

**Symptom:** React app shows blank white screen with no errors

**Diagnosis:**
```bash
# Check browser console for errors
# Common: "Failed to load resource: the server responded with a status of 404"

# Check if static files are served
curl http://<external-ip>/static/js/main.js

# Check Flask static folder
kubectl exec -n sentifinance deployment/sentifinance-backend -- ls -la /app/app/static
```

**Fix:**
```bash
# Ensure frontend build is copied to backend
npm run build
cp -r build/* Backend/app/static/

# Rebuild Docker image
docker build -f Backend/Dockerfile -t sentifinancetwo.azurecr.io/sentifinance-backend:latest .
docker push sentifinancetwo.azurecr.io/sentifinance-backend:latest

# Deploy
kubectl rollout restart deployment/sentifinance-backend -n sentifinance
```

---

## 5. CI/CD Pipeline Errors

### Error: `Workflow didn't trigger on push to dev`

**Symptom:** Push to dev branch but no CI/CD run appears

**Diagnosis:**
```bash
# Check branch name
git branch --show-current
# Should be: dev

# Check remote ref
git log origin/dev --oneline -5

# Check workflow file syntax
gh workflow list
```

**Fix:**
```bash
# Ensure workflows are enabled
gh workflow enable ci.yml
gh workflow enable cd.yml

# Trigger manually
gh workflow run cd.yml

# Force push to trigger
git commit --allow-empty -m "Trigger CI/CD"
git push origin dev
```

**Reference:** WORKFLOW_DEV_BRANCH_CONFIG.md:229-239

---

### Error: `Docker build failed: no space left on device`

**Symptom:**
```
ERROR [internal] load metadata for docker.io/library/python:3.11-slim
error: no space left on device
```

**Cause:** GitHub Actions runner out of disk space

**Fix:**

**Option 1: Clean Docker cache in workflow**
```yaml
# Add to .github/workflows/cd.yml before build step
- name: Clean Docker cache
  run: docker system prune -af --volumes
```

**Option 2: Use Docker layer caching**
```yaml
# Already implemented in cd.yml with buildx cache
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

---

### Error: `Azure login failed`

**Symptom:**
```
Error: Login failed with Error: Unable to parse the service principal:
clientId, clientSecret and tenantId are required parameters.
```

**Cause:** Missing or invalid AZURE_CREDENTIALS secret

**Diagnosis:**
```bash
# Check if GitHub secret exists
gh secret list | grep AZURE_CREDENTIALS
```

**Fix:**
```bash
# Get service principal credentials
az ad sp create-for-rbac \
  --name "sentifinance-github-actions" \
  --role contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/sentifinance2 \
  --sdk-auth

# Copy JSON output and set as GitHub secret
gh secret set AZURE_CREDENTIALS < credentials.json

# Test workflow
gh workflow run cd.yml
```

**Reference:** .github/workflows/cd.yml, RECREATION_GUIDE.md (Phase 5)

---

## 6. News Processing Job Errors

### Error: `CronJob not creating Jobs`

**Symptom:**
```bash
kubectl get cronjobs -n sentifinance
# NAME                        SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE
# news-processing-cronjob     0 2 * * *     False     0        <none>
```

**Diagnosis:**
```bash
# Check CronJob definition
kubectl describe cronjob -n sentifinance news-processing-cronjob

# Check for errors in events
kubectl get events -n sentifinance --sort-by='.lastTimestamp' | grep CronJob
```

**Fix:**
```bash
# Manually trigger job for testing
kubectl create job -n sentifinance \
  --from=cronjob/news-processing-cronjob \
  news-processing-manual-test

# Check job logs
kubectl logs -n sentifinance -l job-name=news-processing-manual-test -f

# Adjust schedule if needed
kubectl edit cronjob -n sentifinance news-processing-cronjob
```

---

### Error: `News processing job OOMKilled`

**Symptom:**
```bash
kubectl get jobs -n sentifinance
# NAME                             COMPLETIONS   DURATION   AGE
# news-processing-job-28362800     0/1           5m         5m

kubectl describe job -n sentifinance news-processing-job-28362800
# Reason: OOMKilled
```

**Cause:** News processor job exceeded memory limits (FinBERT + spaCy loaded)

**Diagnosis:**
```bash
# Check job memory limits
kubectl get cronjob -n sentifinance news-processing-cronjob -o yaml | grep -A5 resources
```

**Fix:**
```yaml
# Edit k8s/news-processing-cronjob.yaml
resources:
  requests:
    memory: "4Gi"      # Increase from 2Gi
    cpu: "1000m"
  limits:
    memory: "8Gi"      # Increase from 4Gi
    cpu: "2000m"

# Apply changes
kubectl apply -f k8s/news-processing-cronjob.yaml

# Test with manual job
kubectl create job -n sentifinance \
  --from=cronjob/news-processing-cronjob \
  news-processing-test
```

**Reference:** Backend/jobs/NEWS-JOB-README.md, k8s/news-processing-cronjob.yaml

---

### Error: `GNews API rate limit exceeded`

**Symptom:**
```
ERROR - GNews API returned 429: Too Many Requests
```

**Cause:** Free tier GNews API limited to 100 requests/day

**Diagnosis:**
```bash
# Check job frequency
kubectl get cronjobs -n sentifinance news-processing-cronjob -o yaml | grep schedule

# Check number of entities being processed
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app, db; from app.models import Entity; \
  app=create_app(); with app.app_context(): print(Entity.query.count())"
```

**Fix:**

**Option 1: Reduce frequency**
```yaml
# Edit k8s/news-processing-cronjob.yaml
schedule: "0 2 * * *"  # Change from "0 */12 * * *" (twice daily) to once daily
```

**Option 2: Process fewer entities per run**
```python
# Edit Backend/jobs/news_processing_job.py
# Add limit to entity query
entities = Entity.query.filter_by(is_active=True).limit(10).all()
```

**Option 3: Upgrade GNews API plan**
```bash
# Update GNEWS_API_KEY in Key Vault with paid tier key
az keyvault secret set \
  --vault-name <vault-name> \
  --name GNEWS-API-KEY \
  --value "<new-api-key>"
```

---

## 7. Azure Infrastructure Errors

### Error: `Terraform apply failed: Error creating resource`

**Symptom:**
```
Error: creating Kubernetes Cluster:
containerservice.ManagedClustersClient#CreateOrUpdate:
Failure responding to request: StatusCode=400
```

**Diagnosis:**
```bash
# Check Terraform state
cd terraform/environments/production
terraform plan

# Check Azure resource quotas
az vm list-usage --location southeastasia -o table
```

**Fix:**
```bash
# Request quota increase if needed
# Azure Portal → Subscriptions → Usage + quotas

# Reduce node count in terraform/modules/aks/variables.tf
variable "node_count" {
  default = 2  # Reduce from 4
}

# Apply changes
terraform apply
```

**Reference:** terraform/README.md, RECREATION_GUIDE.md

---

### Error: `External Secrets not syncing from Key Vault`

**Symptom:**
```bash
kubectl get externalsecret -n sentifinance
# NAME                               STATUS   LAST SYNC   AGE
# sentifinance-external-secrets      Error    2m          10m
```

**Diagnosis:**
```bash
# Check External Secrets Operator logs
kubectl logs -n external-secrets-operator -l app.kubernetes.io/name=external-secrets

# Check SecretStore
kubectl describe secretstore -n sentifinance azure-keyvault-store

# Verify workload identity
kubectl get serviceaccount -n sentifinance default -o yaml | grep azure
```

**Fix:**
```bash
# 1. Verify Key Vault exists and has secrets
az keyvault secret list --vault-name <vault-name> -o table

# 2. Check managed identity has access
az keyvault set-policy \
  --name <vault-name> \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list

# 3. Re-install External Secrets Operator
helm uninstall external-secrets -n external-secrets-operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets-operator --create-namespace

# 4. Re-create ExternalSecret
kubectl delete externalsecret -n sentifinance sentifinance-external-secrets
kubectl apply -f k8s/external-secrets.yaml
```

**Reference:** terraform/SECRETS_SETUP.md, k8s/external-secrets.yaml

---

## Debugging Tools & Commands

### Kubernetes Debugging

```bash
# Interactive shell in running pod
kubectl exec -n sentifinance deployment/sentifinance-backend -it -- /bin/bash

# Run Python command in pod
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app; print(create_app())"

# Port forward to access pod locally
kubectl port-forward -n sentifinance deployment/sentifinance-backend 5001:5001
# Then access http://localhost:5001

# Copy files from pod
kubectl cp -n sentifinance <pod-name>:/app/logs/app.log ./local-app.log

# Copy files to pod
kubectl cp ./local-file.py -n sentifinance <pod-name>:/app/test.py

# Get pod resource usage
kubectl top pods -n sentifinance

# Describe all resources in namespace
kubectl describe all -n sentifinance

# Get events sorted by time
kubectl get events -n sentifinance --sort-by='.lastTimestamp'
```

### Database Debugging

```bash
# Connect to PostgreSQL from pod
kubectl exec -n sentifinance deployment/sentifinance-backend -it -- \
  python -c "from app import create_app, db; app=create_app(); \
  with app.app_context(): print(db.session.execute('SELECT version()').scalar())"

# List all tables
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app, db; app=create_app(); \
  with app.app_context(): print([t for t in db.metadata.sorted_tables])"

# Count rows in table
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app, db; from app.models import News; \
  app=create_app(); with app.app_context(): print(News.query.count())"

# Run SQL query
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app, db; app=create_app(); \
  with app.app_context(): print(db.session.execute('SELECT * FROM user LIMIT 5').fetchall())"
```

### Docker Debugging

```bash
# Test Docker image locally
docker run -it --rm \
  -e DATABASE_URI="sqlite:///test.db" \
  -e SECRET_KEY="test-key" \
  -p 5001:5001 \
  sentifinancetwo.azurecr.io/sentifinance-backend:latest

# Build with no cache
docker build --no-cache -f Backend/Dockerfile -t test-image .

# Inspect image layers
docker history sentifinancetwo.azurecr.io/sentifinance-backend:latest

# Check image size
docker images | grep sentifinance

# Shell into image without running app
docker run -it --rm --entrypoint /bin/bash \
  sentifinancetwo.azurecr.io/sentifinance-backend:latest
```

### Azure CLI Debugging

```bash
# Get AKS cluster info
az aks show --resource-group sentifinance2 --name sentifinance-aks

# List all resources in resource group
az resource list --resource-group sentifinance2 -o table

# Check Azure service health
az monitor metrics list \
  --resource /subscriptions/<sub-id>/resourceGroups/sentifinance2/providers/Microsoft.ContainerService/managedClusters/sentifinance-aks \
  --metric CPUUsagePercentage

# View Key Vault secrets (requires permissions)
az keyvault secret list --vault-name <vault-name> -o table
```

---

## Performance Issues

### Issue: Slow API response times

**Diagnosis:**
```bash
# Check pod CPU/memory usage
kubectl top pods -n sentifinance

# Check HPA status
kubectl get hpa -n sentifinance

# Check number of replicas
kubectl get deployment -n sentifinance sentifinance-backend
```

**Fix:**
```bash
# Scale up manually
kubectl scale deployment -n sentifinance sentifinance-backend --replicas=5

# Check gunicorn worker count
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  grep -r "workers" /app/entrypoint.sh

# Increase workers in entrypoint.sh
# --workers 8  # Increase from 4
```

---

### Issue: Database connection pool exhausted

**Symptom:** Intermittent 500 errors under load

**Diagnosis:**
```bash
# Check active connections
kubectl exec -n sentifinance deployment/sentifinance-backend -- \
  python -c "from app import create_app, db; app=create_app(); \
  with app.app_context(): print(db.session.execute(\
  'SELECT count(*) FROM pg_stat_activity').scalar())"
```

**Fix:**
```python
# Edit Backend/app/config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,        # Increase from 10
    'max_overflow': 40,     # Increase from 20
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# Rebuild and deploy
```

---

### Issue: News processing job taking too long

**Diagnosis:**
```bash
# Check job runtime
kubectl get jobs -n sentifinance -l app=news-processor

# Check logs for bottlenecks
kubectl logs -n sentifinance -l job-name=<job-name> | grep -i "time\|duration"
```

**Fix:**

**Option 1: Process entities in parallel**
```python
# Edit Backend/jobs/news_processing_job.py
# Use multiprocessing or ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(process_entity_news, entities)
```

**Option 2: Reduce entities per run**
```python
# Process only high-priority entities
entities = Entity.query.filter_by(
    is_active=True,
    priority='high'
).all()
```

---

## Getting Help

### Diagnostic Information to Collect

When reporting issues, collect:

```bash
#!/bin/bash
# Generate diagnostic report

echo "=== Kubernetes Pods ===" > diagnostic-report.txt
kubectl get pods -n sentifinance >> diagnostic-report.txt

echo "\n=== Recent Logs ===" >> diagnostic-report.txt
kubectl logs -n sentifinance -l app=sentifinance-backend --tail=100 >> diagnostic-report.txt

echo "\n=== Pod Events ===" >> diagnostic-report.txt
kubectl describe pods -n sentifinance >> diagnostic-report.txt

echo "\n=== Service Status ===" >> diagnostic-report.txt
kubectl get service -n sentifinance >> diagnostic-report.txt

echo "\n=== Recent CI/CD Runs ===" >> diagnostic-report.txt
gh run list --limit 5 >> diagnostic-report.txt

echo "\n=== Git Status ===" >> diagnostic-report.txt
git status >> diagnostic-report.txt
git log --oneline -5 >> diagnostic-report.txt

cat diagnostic-report.txt
```

### Related Documentation

- **Full Infrastructure Setup:** RECREATION_GUIDE.md
- **Database Schema:** DATABASE_SCHEMA.md
- **Backend API:** Backend/Backend.md
- **Kubernetes Deployment:** k8s/README.md
- **Terraform Infrastructure:** terraform/README.md
- **CI/CD Configuration:** WORKFLOW_DEV_BRANCH_CONFIG.md
- **News Processing Job:** Backend/jobs/NEWS-JOB-README.md
- **PostgreSQL Setup:** terraform/POSTGRESQL_SETUP.md
- **Secrets Management:** terraform/SECRETS_SETUP.md

### External Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **Kubernetes Documentation:** https://kubernetes.io/docs/
- **Azure Kubernetes Service:** https://learn.microsoft.com/en-us/azure/aks/
- **Terraform Azure Provider:** https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- **GitHub Actions:** https://docs.github.com/en/actions

---

**Last Updated:** December 11, 2025
