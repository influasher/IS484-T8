#!/bin/bash

# ===================================================================
# Azure Monitor Setup Script for News Processor CronJob
# ===================================================================
#
# This script sets up comprehensive monitoring and alerting for the
# news-processor microservice running in AKS via Azure Container Instances
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - kubectl configured with AKS cluster access
# - jq installed for JSON parsing
#
# Usage:
#   chmod +x scripts/setup-monitoring.sh
#   ./scripts/setup-monitoring.sh
#
# ===================================================================

set -e  # Exit on error

# ===================================================================
# Configuration Variables
# ===================================================================

RESOURCE_GROUP="${AKS_RESOURCE_GROUP:-sentifinance-rg}"
LOCATION="${AZURE_LOCATION:-eastus}"
WORKSPACE_NAME="sentifinance-logs"
ACTION_GROUP_NAME="news-processor-alerts"
ACTION_GROUP_SHORT_NAME="np-alerts"
ALERT_EMAIL="${ALERT_EMAIL:-admin@example.com}"
NAMESPACE="sentifinance"

echo "====================================================================="
echo "Azure Monitor Setup for News Processor"
echo "====================================================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Log Analytics Workspace: $WORKSPACE_NAME"
echo "Alert Email: $ALERT_EMAIL"
echo "====================================================================="
echo ""

# ===================================================================
# Step 1: Create Log Analytics Workspace
# ===================================================================

echo "[1/6] Creating Log Analytics Workspace..."

WORKSPACE_EXISTS=$(az monitor log-analytics workspace list \
  --resource-group "$RESOURCE_GROUP" \
  --query "[?name=='$WORKSPACE_NAME'].name" -o tsv 2>/dev/null || echo "")

if [ -z "$WORKSPACE_EXISTS" ]; then
  az monitor log-analytics workspace create \
    --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$WORKSPACE_NAME" \
    --location "$LOCATION" \
    --retention-time 30 \
    --tags "component=monitoring" "service=news-processor"
  echo "✅ Log Analytics Workspace created: $WORKSPACE_NAME"
else
  echo "ℹ️  Log Analytics Workspace already exists: $WORKSPACE_NAME"
fi

# ===================================================================
# Step 2: Get Workspace Credentials
# ===================================================================

echo "[2/6] Retrieving workspace credentials..."

WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$WORKSPACE_NAME" \
  --query customerId -o tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$WORKSPACE_NAME" \
  --query primarySharedKey -o tsv)

echo "✅ Workspace ID: $WORKSPACE_ID"
echo "✅ Workspace Key: [REDACTED]"

# ===================================================================
# Step 3: Update Kubernetes CronJob with Workspace Credentials
# ===================================================================

echo "[3/6] Updating CronJob annotations..."

# Create a temporary file with updated annotations
TEMP_FILE=$(mktemp)
cat k8s/news-processing-cronjob.yaml | \
  sed "s|# virtual-kubelet.io/log-analytics-workspace-id:.*|virtual-kubelet.io/log-analytics-workspace-id: \"$WORKSPACE_ID\"|" | \
  sed "s|# virtual-kubelet.io/log-analytics-workspace-key:.*|virtual-kubelet.io/log-analytics-workspace-key: \"$WORKSPACE_KEY\"|" \
  > "$TEMP_FILE"

# Apply the updated CronJob
kubectl apply -f "$TEMP_FILE" --namespace="$NAMESPACE"
rm "$TEMP_FILE"

echo "✅ CronJob updated with Log Analytics credentials"

# ===================================================================
# Step 4: Create Action Group for Alerts
# ===================================================================

echo "[4/6] Creating Action Group for email alerts..."

ACTION_GROUP_EXISTS=$(az monitor action-group list \
  --resource-group "$RESOURCE_GROUP" \
  --query "[?name=='$ACTION_GROUP_NAME'].name" -o tsv 2>/dev/null || echo "")

if [ -z "$ACTION_GROUP_EXISTS" ]; then
  az monitor action-group create \
    --name "$ACTION_GROUP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --short-name "$ACTION_GROUP_SHORT_NAME" \
    --email-receiver name=admin email="$ALERT_EMAIL"
  echo "✅ Action Group created: $ACTION_GROUP_NAME"
else
  echo "ℹ️  Action Group already exists: $ACTION_GROUP_NAME"
fi

# ===================================================================
# Step 5: Create Alert Rules
# ===================================================================

echo "[5/6] Creating alert rules..."

# Get workspace resource ID
WORKSPACE_RESOURCE_ID=$(az monitor log-analytics workspace show \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$WORKSPACE_NAME" \
  --query id -o tsv)

# Alert 1: Job Failure
echo "  - Creating alert: Job Failure..."
az monitor scheduled-query create \
  --name "news-processor-job-failure" \
  --resource-group "$RESOURCE_GROUP" \
  --scopes "$WORKSPACE_RESOURCE_ID" \
  --condition "count 'Heartbeat' > 0" \
  --condition-query "ContainerInstanceLog_CL | where Name_s == 'news-processor' | where Message contains 'ERROR' or Message contains 'FAILED' | summarize FailureCount = count() by bin(TimeGenerated, 5m) | where FailureCount > 0" \
  --description "Alerts when news processor job fails" \
  --evaluation-frequency 5m \
  --window-size 5m \
  --severity 2 \
  --action-groups "$ACTION_GROUP_NAME" \
  --auto-mitigate true \
  2>/dev/null || echo "⚠️  Alert creation requires Azure Monitor permissions"

# Alert 2: Job Not Running (Missed Schedule)
echo "  - Creating alert: Missed Schedule..."
az monitor scheduled-query create \
  --name "news-processor-missed-schedule" \
  --resource-group "$RESOURCE_GROUP" \
  --scopes "$WORKSPACE_RESOURCE_ID" \
  --condition "count 'Heartbeat' > 0" \
  --condition-query "ContainerInstanceLog_CL | where Name_s == 'news-processor' | where Message contains 'Processing started' | summarize LastRun = max(TimeGenerated) | where LastRun < ago(3d)" \
  --description "Alerts when news processor hasn't run in 3 days" \
  --evaluation-frequency 1h \
  --window-size 3d \
  --severity 1 \
  --action-groups "$ACTION_GROUP_NAME" \
  --auto-mitigate true \
  2>/dev/null || echo "⚠️  Alert creation requires Azure Monitor permissions"

echo "✅ Alert rules created (or skipped if permissions insufficient)"

# ===================================================================
# Step 6: Apply Monitoring ConfigMap
# ===================================================================

echo "[6/6] Applying monitoring ConfigMap..."

kubectl apply -f k8s/news-processor-monitoring.yaml --namespace="$NAMESPACE"

echo "✅ Monitoring ConfigMap applied"

# ===================================================================
# Summary
# ===================================================================

echo ""
echo "====================================================================="
echo "✅ Monitoring Setup Complete!"
echo "====================================================================="
echo ""
echo "📊 View logs in Azure Portal:"
echo "   https://portal.azure.com/#blade/Microsoft_Azure_Monitoring/AzureMonitoringBrowseBlade/logs"
echo ""
echo "🔔 Alert email will be sent to: $ALERT_EMAIL"
echo ""
echo "📈 Next steps:"
echo "   1. Test the CronJob: kubectl create job --from=cronjob/news-processor test-job -n $NAMESPACE"
echo "   2. View logs: kubectl logs -n $NAMESPACE job/test-job"
echo "   3. Check Azure Monitor: Wait 5-10 minutes for logs to appear"
echo "   4. Create custom dashboard in Azure Portal"
echo ""
echo "🔍 Useful commands:"
echo "   - View CronJob status: kubectl get cronjobs -n $NAMESPACE"
echo "   - View recent jobs: kubectl get jobs -n $NAMESPACE"
echo "   - View pod logs: kubectl logs -n $NAMESPACE -l app=news-processor"
echo "   - Test alert: kubectl create job --from=cronjob/news-processor test-failure -n $NAMESPACE"
echo ""
echo "💰 Cost estimate (spot instances):"
echo "   - Memory: 5GB × 2 hours × 2 runs/week × 4 weeks = 80 GB-hours"
echo "   - CPU: 2 vCPU × 2 hours × 2 runs/week × 4 weeks = 32 vCPU-hours"
echo "   - Estimated monthly cost: $5-10 (vs $30-50 for regular instances)"
echo ""
echo "====================================================================="
