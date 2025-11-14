#!/bin/bash

# ===================================================================
# AKS Deployment Diagnostic Script
# ===================================================================
#
# This script helps diagnose why the backend deployment is failing
# in Azure Kubernetes Service (AKS).
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - kubectl installed
# - Access to the AKS cluster
#
# Usage:
#   chmod +x scripts/diagnose-aks-deployment.sh
#   ./scripts/diagnose-aks-deployment.sh
#
# ===================================================================

set -e  # Exit on error (disabled for diagnostic purposes)
set +e  # Continue on error to gather all diagnostics

echo "====================================================================="
echo "AKS Deployment Diagnostic Tool"
echo "====================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NAMESPACE="sentifinance"
DEPLOYMENT="sentifinance-backend"

# ===================================================================
# Step 1: Check kubectl connectivity
# ===================================================================

echo "[1/10] Checking kubectl connectivity..."
if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✅ kubectl is connected to cluster${NC}"
else
    echo -e "${RED}❌ kubectl is NOT connected to cluster${NC}"
    echo ""
    echo "Please run:"
    echo "  az aks get-credentials --resource-group <your-rg> --name <your-cluster> --overwrite-existing"
    exit 1
fi

# ===================================================================
# Step 2: Check namespace exists
# ===================================================================

echo ""
echo "[2/10] Checking namespace..."
if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✅ Namespace '$NAMESPACE' exists${NC}"
else
    echo -e "${RED}❌ Namespace '$NAMESPACE' does not exist${NC}"
    echo "Create it with: kubectl create namespace $NAMESPACE"
    exit 1
fi

# ===================================================================
# Step 3: Check deployment status
# ===================================================================

echo ""
echo "[3/10] Checking deployment status..."
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o wide

echo ""
echo "Deployment details:"
kubectl describe deployment $DEPLOYMENT -n $NAMESPACE | grep -A 10 "Conditions:"

# ===================================================================
# Step 4: Check pods status
# ===================================================================

echo ""
echo "[4/10] Checking pods..."
echo ""
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT -o wide

echo ""
echo "Pod count by status:"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT --no-headers | awk '{print $3}' | sort | uniq -c

# ===================================================================
# Step 5: Check pod events
# ===================================================================

echo ""
echo "[5/10] Checking pod events (last 20)..."
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -20

# ===================================================================
# Step 6: Check failing pod logs
# ===================================================================

echo ""
echo "[6/10] Checking logs from failing pods..."

# Get pods that are not Running
FAILING_PODS=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT --no-headers | grep -v "Running" | awk '{print $1}' || echo "")

if [ -z "$FAILING_PODS" ]; then
    echo -e "${GREEN}No failing pods found${NC}"
else
    for POD in $FAILING_PODS; do
        echo ""
        echo -e "${YELLOW}Pod: $POD${NC}"
        echo "Status:"
        kubectl get pod $POD -n $NAMESPACE

        echo ""
        echo "Describe (last 30 lines):"
        kubectl describe pod $POD -n $NAMESPACE | tail -30

        echo ""
        echo "Logs (last 50 lines):"
        kubectl logs $POD -n $NAMESPACE --tail=50 2>&1 || echo "No logs available"

        echo ""
        echo "Previous logs (if pod restarted):"
        kubectl logs $POD -n $NAMESPACE --previous --tail=50 2>&1 || echo "No previous logs"

        echo "---"
    done
fi

# ===================================================================
# Step 7: Check ReplicaSet status
# ===================================================================

echo ""
echo "[7/10] Checking ReplicaSets..."
kubectl get replicaset -n $NAMESPACE -l app=$DEPLOYMENT -o wide

# ===================================================================
# Step 8: Check if image is accessible
# ===================================================================

echo ""
echo "[8/10] Checking image configuration..."
IMAGE=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')
echo "Current image: $IMAGE"

echo ""
echo "Image pull secrets:"
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.imagePullSecrets}'

echo ""
echo ""
echo "Checking image pull events:"
kubectl get events -n $NAMESPACE | grep -i "pull\|image" | tail -10

# ===================================================================
# Step 9: Check resource constraints
# ===================================================================

echo ""
echo "[9/10] Checking resource constraints..."

echo "Deployment resource requests/limits:"
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources}' | jq '.'

echo ""
echo "Node capacity:"
kubectl top nodes 2>&1 || echo "Metrics server not available"

echo ""
echo "Pod resource usage:"
kubectl top pods -n $NAMESPACE 2>&1 || echo "Metrics server not available"

# ===================================================================
# Step 10: Check readiness/liveness probes
# ===================================================================

echo ""
echo "[10/10] Checking health probes..."

echo "Readiness probe:"
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}' | jq '.'

echo ""
echo "Liveness probe:"
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}' | jq '.'

# ===================================================================
# Summary
# ===================================================================

echo ""
echo "====================================================================="
echo "Diagnostic Summary"
echo "====================================================================="

# Count pods by status
RUNNING=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT --no-headers 2>/dev/null | grep -c "Running" || echo 0)
PENDING=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT --no-headers 2>/dev/null | grep -c "Pending" || echo 0)
ERROR=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT --no-headers 2>/dev/null | grep -c "Error\|CrashLoopBackOff\|ImagePullBackOff" || echo 0)

echo "Pod Status:"
echo "  Running: $RUNNING"
echo "  Pending: $PENDING"
echo "  Error/CrashLoop: $ERROR"

echo ""
echo "Common Issues to Check:"
echo "1. Image Pull Errors:"
echo "   - Check if ACR credentials are configured"
echo "   - Verify image exists in registry"
echo "   - Check imagePullSecrets"
echo ""
echo "2. Application Crashes:"
echo "   - Check pod logs above for Python tracebacks"
echo "   - Verify environment variables are set"
echo "   - Check if database is accessible"
echo ""
echo "3. Resource Constraints:"
echo "   - OOMKilled = increase memory limits"
echo "   - Evicted = node has insufficient resources"
echo ""
echo "4. Readiness Probe Failures:"
echo "   - App takes too long to start"
echo "   - Increase initialDelaySeconds"
echo "   - Check if health endpoint is working"
echo ""
echo "====================================================================="
echo ""
echo "Next Steps:"
echo "1. Review the logs and events above"
echo "2. Fix the identified issue"
echo "3. Redeploy: git push origin dev"
echo ""
echo "Manual Commands:"
echo "  # Watch pods in real-time"
echo "  kubectl get pods -n $NAMESPACE -w"
echo ""
echo "  # Get logs from specific pod"
echo "  kubectl logs -f <pod-name> -n $NAMESPACE"
echo ""
echo "  # Describe specific pod"
echo "  kubectl describe pod <pod-name> -n $NAMESPACE"
echo ""
echo "  # Delete failed pods (will recreate)"
echo "  kubectl delete pod <pod-name> -n $NAMESPACE"
echo ""
echo "====================================================================="
