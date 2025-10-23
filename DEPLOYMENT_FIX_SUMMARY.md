# Deployment Fix Summary - October 23, 2025

## Issues Identified and Fixed

### 1. **ImagePullBackOff** (RESOLVED ✅)
- **Root Cause**: ACR was never properly attached to AKS
- **Fix**: Ran `az aks update --attach-acr sentifinancetwo` + added `imagePullSecrets: acr-secret`
- **Status**: Pods now successfully pull images

### 2. **CrashLoopBackOff** (RESOLVED ✅)
- **Root Cause**: Dockerfile CMD used `uv run python run.py` which rebuilds package on every start
- **Fix**: Changed CMD to `.venv/bin/python run.py` (uses pre-built venv)
- **Status**: Containers now start without rebuild delay

### 3. **App Startup Hangs** (PARTIALLY RESOLVED ⚠️)
- **Root Cause**: FinBERT model loading takes 3+ minutes and consumes significant memory
- **Fixes Applied**:
  - Increased readinessProbe initialDelay: 45s → 180s (3 minutes)
  - Increased livenessProbe initialDelay: 75s → 240s (4 minutes)
  - Increased memory limits: 512Mi → 1Gi (prevent OOM during model load)
  - Increased memory requests: 256Mi → 512Mi
  - Increased CPU limits: 250m → 500m
- **Status**: Waiting to test

### 4. **CD Workflow Timeout** (RESOLVED ✅)
- **Root Cause**: Health check timeout (300s) too short for image pull + model loading
- **Fix**: Increased timeout from 300s → 600s (10 minutes)
- **Status**: Ready to deploy

## Current Configuration

### Dockerfile
```dockerfile
CMD [".venv/bin/python", "run.py"]  # Direct venv execution
```

### Deployment Resources
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "100m"
  limits:
    memory: "1Gi"     # Sufficient for FinBERT model
    cpu: "500m"
```

### Health Probes
```yaml
readinessProbe:
  initialDelaySeconds: 180  # 3 minutes for model loading
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 6

livenessProbe:
  initialDelaySeconds: 240  # 4 minutes before first check
  periodSeconds: 10
```

### CD Workflow
```yaml
kubectl rollout status --timeout=600s  # 10 minutes
```

## Timeline Expectations

1. **Image Pull**: ~5 minutes (5.9GB image)
2. **Container Start**: <10 seconds
3. **Model Loading**: ~3 minutes (FinBERT initialization)
4. **App Ready**: 180 seconds after container start
5. **Total Time**: ~8-10 minutes from deployment to ready

## Verification Checklist

- [x] ACR integration working (imagePullSecrets configured)
- [x] Dockerfile CMD fixed (no uv rebuild)
- [x] Probe delays sufficient (180s/240s)
- [x] Memory limits increased (1Gi)
- [x] CD timeout increased (600s)
- [x] HPA configured (min: 1, max: 3)
- [x] Node capacity adequate (4 nodes available)
- [ ] **PENDING**: Test actual deployment

## Potential Risks

### 1. Memory Consumption
- Current pods using 452Mi without serving traffic
- May spike higher during model loading
- Mitigation: Increased limit to 1Gi

### 2. Node Capacity
- Nodes at 75-95% memory usage
- Single replica with 512Mi request should fit
- Mitigation: HPA will scale only if resources available

### 3. Startup Time
- Model loading is I/O and CPU intensive
- May take longer on constrained nodes
- Mitigation: 180s readiness delay + 240s liveness delay

## Next Steps

1. Commit memory limit changes
2. Push to trigger CD workflow
3. Monitor deployment for 10-15 minutes
4. Verify pod becomes ready
5. Test API endpoint responds

## Fallback Plan

If deployment still fails:
1. Check pod logs: `kubectl logs -n sentifinance <pod-name>`
2. Describe pod events: `kubectl describe pod -n sentifinance <pod-name>`
3. Consider lazy model loading (load on first request instead of startup)
4. Add startup probe with longer failureThreshold * periodSeconds
