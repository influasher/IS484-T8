# 🚀 Fast CD Testing Guide

## Quick Local Validation (< 5 seconds)

Run before every commit to catch issues early:

```bash
# Option 1: Run the script directly
./.github/scripts/test_cd_locally.sh

# Option 2: Use the alias (faster to type)
test-cd
```

**What it checks:**
- ✅ Workflow YAML syntax
- ✅ Kubernetes manifest validity
- ✅ Required secrets are referenced
- ✅ Shell script syntax
- ✅ Docker build context
- ✅ AKS connectivity (optional)

---

## Fast Iteration Workflow

### 1. Make Changes
Edit your files (workflows, K8s manifests, etc.)

### 2. Validate Locally
```bash
test-cd
```

### 3. Commit and Push
```bash
git add .
git commit -m "fix: update deployment config"
git push origin dev
```

### 4. Trigger CD Manually (Skip CI)
```bash
# Skip waiting for CI to complete
gh workflow run cd.yml --ref dev
```

### 5. Watch Logs in Real-Time
```bash
# Follow the workflow as it runs
gh run watch

# OR open in browser
gh run view --web
```

---

## Testing Specific Components

### Test Kubernetes Manifests Only
```bash
kubectl apply --dry-run=client -f k8s/deployment.yaml
kubectl apply --dry-run=client -f k8s/service.yaml
```

### Test Docker Build Locally
```bash
cd Backend
docker build -t sentifinance-backend:test .
```

### Test Secret References
```bash
grep "secrets\." .github/workflows/cd.yml | sort | uniq
```

### Verify GitHub Secrets
```bash
gh secret list --repo influasher/IS484-T8
```

---

## Common Issues & Fixes

### Issue: "YAML syntax error"
**Fix:** Check indentation in workflow file
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/cd.yml'))"
```

### Issue: "Invalid K8s manifest"
**Fix:** Validate with kubectl
```bash
kubectl apply --dry-run=client -f k8s/deployment.yaml
```

### Issue: "Secret not found"
**Fix:** Add missing secret to GitHub
```bash
gh secret set SECRET_NAME --repo influasher/IS484-T8
# Paste the secret value when prompted
```

### Issue: "Not connected to AKS"
**Fix:** Get AKS credentials
```bash
az aks get-credentials \
  --resource-group $(gh secret list --repo influasher/IS484-T8 | grep AKS_RESOURCE_GROUP | awk '{print $2}') \
  --name $(gh secret list --repo influasher/IS484-T8 | grep AKS_CLUSTER_NAME | awk '{print $2}')
```

---

## Useful Aliases

Add these to your `~/.zshrc` for even faster testing:

```bash
# Already added
alias test-cd='bash .github/scripts/test_cd_locally.sh'

# Additional helpful aliases
alias cd-logs='gh run watch'
alias cd-run='gh workflow run cd.yml --ref dev'
alias cd-status='gh run list --workflow=cd.yml --limit 5'
alias k8s-status='kubectl get all -n sentifinance'
alias k8s-logs='kubectl logs -n sentifinance -l app=sentifinance-backend --tail=50 -f'
```

Then reload:
```bash
source ~/.zshrc
```

---

## Speed Comparison

| Method | Time | Use Case |
|--------|------|----------|
| `test-cd` | ~2-5s | Before every commit |
| Manual workflow trigger | ~3-5min | Test CD without CI |
| Push to dev (full CI+CD) | ~8-12min | Full integration test |
| Local Docker build | ~1-3min | Test container build |

---

## Workflow Triggers

Your CD workflow runs when:

1. ✅ **Manual dispatch** - `gh workflow run cd.yml --ref dev`
2. ✅ **Push to dev** - `git push origin dev`
3. ✅ **After CI success** - Automatically when CI pipeline completes

You can skip CI by using manual dispatch (#1).

---

## Pro Tips

### Skip pushing to test locally
```bash
# Stash changes, test, then pop
git stash
test-cd
git stash pop
```

### Test multiple manifests at once
```bash
for file in k8s/*.yaml; do 
  echo "Testing $file..."
  kubectl apply --dry-run=client -f "$file" || echo "❌ Failed: $file"
done
```

### Quick secret check
```bash
# See when secrets were last updated
gh secret list --repo influasher/IS484-T8
```

### View recent workflow runs
```bash
gh run list --workflow=cd.yml --limit 10
```

### Cancel a running workflow
```bash
gh run cancel <run-id>
# Or cancel the latest
gh run list --workflow=cd.yml --limit 1 --json databaseId -q '.[0].databaseId' | xargs gh run cancel
```

---

## Emergency: Rollback Deployment

```bash
# Get previous image SHA
gh run list --workflow=cd.yml --limit 5

# Update deployment to use previous image
kubectl set image deployment/sentifinance-backend \
  sentifinance-backend=sentifinacetwo.azurecr.io/sentifinance-backend:<previous-sha> \
  -n sentifinance

# OR rollback to previous revision
kubectl rollout undo deployment/sentifinance-backend -n sentifinance
```

---

## Next Steps After This Guide

1. ✅ Run `test-cd` before every commit
2. ✅ Use `gh workflow run cd.yml --ref dev` to skip CI when testing CD changes
3. ✅ Monitor with `gh run watch`
4. ✅ Check logs with `kubectl logs -n sentifinance -l app=sentifinance-backend`
5. ✅ Get LoadBalancer IP: `kubectl get svc backend-service -n sentifinance`

Happy deploying! 🚀
