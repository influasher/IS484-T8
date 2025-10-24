# Rollback Instructions - Microservices Refactor

## Safe Rollback Point Created ✅

A git tag `before-microservices-refactor` has been created and pushed to the remote repository. This marks the last stable commit **before** the microservices refactoring.

---

## When to Rollback

Rollback if you experience:

- ❌ Backend fails to build after refactoring
- ❌ Missing dependencies causing import errors
- ❌ Critical functionality broken
- ❌ News processor doesn't work as expected
- ❌ Team decides to revert to monolithic architecture

---

## Rollback Methods

### **Method 1: Full Rollback (Recommended if completely broken)**

This resets your local branch to the tagged commit:

```bash
# 1. Reset to the tag (discards all refactoring changes)
git reset --hard before-microservices-refactor

# 2. Force push to remote (WARNING: This rewrites history!)
git push origin dev --force

# 3. Verify rollback
git log --oneline -5
```

⚠️ **WARNING**: This will **permanently delete** all commits after the tag. Only use if refactoring is completely broken.

---

### **Method 2: Revert Commit (Safer - Creates new commit)**

This creates a **new commit** that undoes the refactoring (preserves history):

```bash
# 1. Get the commit hash of the refactoring commit
git log --oneline -5

# 2. Revert the refactoring commit (replace <commit-hash>)
git revert <commit-hash> --no-edit

# 3. Push the revert commit
git push origin dev

# 4. Optionally: Revert the revert later if you want to try again
git revert <revert-commit-hash>
```

✅ **SAFER**: Preserves git history, can be undone later.

---

### **Method 3: Create New Branch from Tag (Test Rollback)**

Test the rollback without affecting the dev branch:

```bash
# 1. Create a new branch from the tag
git checkout -b rollback-test before-microservices-refactor

# 2. Test that everything works
# ... run tests, deploy, verify ...

# 3. If satisfied, merge to dev
git checkout dev
git reset --hard rollback-test
git push origin dev --force

# 4. Or just switch back if testing
git checkout dev
```

✅ **SAFEST**: Test before affecting dev branch.

---

## What Gets Rolled Back

### **Code Changes Reverted:**

1. **Backend Routes** (`Backend/app/routes/sentiment_analysis.py`):
   - ✅ Restores `POST /sentiment/analyze` with full ML functionality
   - ✅ Restores `POST /sentiment/entity` with full entity analysis

2. **Dependencies** (`Backend/pyproject.toml`):
   - ✅ Re-adds heavy ML dependencies:
     - crawl4ai, playwright, spacy, torch, transformers, shap

3. **Dockerfile** (`Backend/Dockerfile`):
   - ✅ Restores spaCy model download
   - ✅ Restores crawl4ai-setup
   - ✅ Backend image back to 5.8GB

4. **News Processor Files** (removed):
   - ❌ `Backend/jobs/news_processing_job.py` - deleted
   - ❌ `Backend/Dockerfile.news-processor` - deleted
   - ❌ `k8s/news-processing-cronjob.yaml` - deleted

5. **CI/CD** (`.github/workflows/cd.yml`):
   - ✅ Removes news-processor build steps
   - ✅ Removes database secrets creation

### **Infrastructure Reverted:**

- Backend deployment back to original memory limits
- No separate news processor CronJob
- All functionality in monolithic backend

---

## After Rollback - Fix Instructions

If you rolled back, here's how to fix the **original issues** before trying again:

### **Issue: Backend OOMKilled**

**Original Problem:**
- Exit Code 137 (OOM kill)
- 5.8GB image too heavy for 1536Mi memory limit

**Fix Options:**

1. **Increase Memory (Quick Fix)**:
   ```yaml
   # In k8s/deployment.yaml
   resources:
     requests:
       memory: "2Gi"
     limits:
       memory: "4Gi"
   ```

2. **Deploy to Virtual Node**:
   ```yaml
   # In k8s/deployment.yaml
   nodeSelector:
     kubernetes.io/role: agent
     type: virtual-kubelet
   tolerations:
   - key: virtual-kubelet.io/provider
     operator: Exists
   ```

3. **Reduce Replicas**:
   ```yaml
   # In k8s/deployment.yaml
   spec:
     replicas: 1  # Down from 3
   ```

### **Issue: Liveness Probe Failures**

**Original Problem:**
- Probes fail before ML models finish loading
- Initial delays too short

**Fix:**
```yaml
# In k8s/deployment.yaml
readinessProbe:
  initialDelaySeconds: 180  # 3 minutes (was 30s)
livenessProbe:
  initialDelaySeconds: 240  # 4 minutes (was 60s)
```

---

## Verify Rollback Success

After rolling back, verify everything works:

```bash
# 1. Check git status
git log --oneline -5
git diff origin/dev

# 2. Check files restored
ls Backend/app/routes/sentiment_analysis.py
cat Backend/pyproject.toml | grep torch
cat Backend/Dockerfile | grep spacy

# 3. Verify news processor files removed
ls Backend/jobs/  # Should not exist
ls k8s/news-processing-cronjob.yaml  # Should not exist

# 4. Build and test locally
cd Backend
docker build -t test-backend .

# 5. Deploy and verify
git push origin dev
# Watch GitHub Actions CD workflow
gh run watch
```

---

## Re-attempt Refactoring

If you rolled back and want to try the refactoring again later:

### **Option A: Cherry-pick from Failed Refactor**

```bash
# 1. Find the refactoring commit hash
git log --all --oneline | grep microservices

# 2. Cherry-pick it
git cherry-pick <refactor-commit-hash>

# 3. Fix issues and commit
```

### **Option B: Start Fresh with Fixes**

1. Review what went wrong in deployment logs
2. Fix those specific issues in the code
3. Re-apply the refactoring manually with fixes included
4. Create a new tag: `before-microservices-refactor-v2`

---

## Contact Points

If you need help with rollback:

1. **Check logs first**: 
   ```bash
   kubectl logs -n sentifinance deployment/sentifinance-backend --tail=100
   ```

2. **Review error events**:
   ```bash
   kubectl describe pod -n sentifinance <pod-name>
   ```

3. **Review this guide**: `BACKEND_REFACTOR_GUIDE.md`

4. **Check CD workflow**: 
   ```bash
   gh run list --workflow=cd.yml --limit 5
   gh run view <run-id> --log-failed
   ```

---

## Summary

You now have **3 rollback options**:

1. ⚡ **Full Rollback**: `git reset --hard before-microservices-refactor` (fastest, loses history)
2. ✅ **Revert Commit**: `git revert <hash>` (preserves history, safest)
3. 🧪 **Test Branch**: `git checkout -b rollback-test before-microservices-refactor` (test first)

The tag `before-microservices-refactor` is **permanent** and available to your entire team on GitHub.

**Rollback Command (Quick Reference):**
```bash
git reset --hard before-microservices-refactor && git push origin dev --force
```
