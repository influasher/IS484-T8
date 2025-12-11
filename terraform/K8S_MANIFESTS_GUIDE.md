# Kubernetes Manifests Configuration Guide

This guide explains how to configure and deploy all Kubernetes resources for the SentiFinance application after Terraform has created the infrastructure.

## Prerequisites

- ✅ Terraform has created AKS cluster and all infrastructure
- ✅ PostgreSQL database is created and accessible
- ✅ Key Vault secrets are configured
- ✅ `kubectl` is installed and configured
- ✅ AKS credentials are obtained

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group sentifinance.azurecr.io \
  --name sentifinance-k8 \
  --overwrite-existing

# Verify connection
kubectl get nodes
```

---

## Deployment Overview

The deployment consists of these components:

1. **Namespace** - Isolate application resources
2. **External Secrets Operator (ESO)** - Sync secrets from Key Vault
3. **ServiceAccount** - For workload identity
4. **SecretStore** - Connect ESO to Key Vault
5. **ExternalSecret** - Define which secrets to sync
6. **Deployment** - Application pods
7. **Service** - LoadBalancer to expose application
8. **HorizontalPodAutoscaler (HPA)** - Auto-scaling
9. **PodDisruptionBudget (PDB)** - High availability

---

## Step-by-Step Deployment

### Step 1: Create Namespace

**File: `k8s/namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sentifinance
  labels:
    name: sentifinance
    environment: production
```

**Deploy:**

```bash
kubectl apply -f k8s/namespace.yaml

# Verify
kubectl get namespace sentifinance
```

---

### Step 2: Install External Secrets Operator

**Install ESO using Helm:**

```bash
# Add Helm repo
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install ESO
helm install external-secrets \
  external-secrets/external-secrets \
  --namespace external-secrets-operator \
  --create-namespace \
  --set installCRDs=true

# Verify ESO is running
kubectl get pods -n external-secrets-operator

# Expected output:
# NAME                                                READY   STATUS
# external-secrets-...                                1/1     Running
# external-secrets-cert-controller-...                1/1     Running
# external-secrets-webhook-...                        1/1     Running
```

---

### Step 3: Create ServiceAccount with Workload Identity

**File: `k8s/serviceaccount.yaml`**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: external-secrets-sa
  namespace: sentifinance
  annotations:
    azure.workload.identity/client-id: "<ESO_IDENTITY_CLIENT_ID>"
    azure.workload.identity/tenant-id: "<AZURE_TENANT_ID>"
```

**Get the values from Terraform:**

```bash
# Get ESO identity client ID
cd terraform/environments/production
terraform output eso_identity_client_id

# Get Azure tenant ID
az account show --query tenantId -o tsv
```

**Update the YAML with actual values, then deploy:**

```bash
# Replace <ESO_IDENTITY_CLIENT_ID> with actual value
kubectl apply -f k8s/serviceaccount.yaml

# Verify
kubectl describe sa external-secrets-sa -n sentifinance
```

---

### Step 4: Create SecretStore

**File: `k8s/secretstore.yaml`**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: azure-secret-store
  namespace: sentifinance
spec:
  provider:
    azurekv:
      authType: WorkloadIdentity
      vaultUrl: https://sentifinance-key-vault.vault.azure.net/
      serviceAccountRef:
        name: external-secrets-sa
```

**Deploy:**

```bash
kubectl apply -f k8s/secretstore.yaml

# Verify
kubectl get secretstore -n sentifinance
kubectl describe secretstore azure-secret-store -n sentifinance

# Check for "Valid" status
```

---

### Step 5: Create ExternalSecret

**File: `k8s/externalsecret.yaml`**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: sentifinance-secrets
  namespace: sentifinance
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: azure-secret-store
    kind: SecretStore
  target:
    name: sentifinance-app-secrets
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_URI
      remoteRef:
        key: DATABASE-URI
    - secretKey: JWT_SECRET_KEY
      remoteRef:
        key: JWT-SECRET-KEY
    - secretKey: SECRET_KEY
      remoteRef:
        key: SECRET-KEY
```

**Deploy:**

```bash
kubectl apply -f k8s/externalsecret.yaml

# Verify ExternalSecret is syncing
kubectl get externalsecret -n sentifinance

# Check status (should show "SecretSynced")
kubectl describe externalsecret sentifinance-secrets -n sentifinance

# Verify Kubernetes secret was created
kubectl get secret sentifinance-app-secrets -n sentifinance

# View secret keys (not values)
kubectl describe secret sentifinance-app-secrets -n sentifinance
```

---

### Step 6: Deploy Application

**File: `k8s/deployment.yaml`**

Update your existing deployment.yaml with correct values:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentifinance-backend
  namespace: sentifinance
  labels:
    app: sentifinance-backend
    environment: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sentifinance-backend
  template:
    metadata:
      labels:
        app: sentifinance-backend
        environment: production
    spec:
      containers:
      - name: backend
        image: sentifinancetwo.azurecr.io/sentifinance-backend:latest
        ports:
        - containerPort: 5000
          name: http
          protocol: TCP
        env:
        - name: DATABASE_URI
          valueFrom:
            secretKeyRef:
              name: sentifinance-app-secrets
              key: DATABASE_URI
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: sentifinance-app-secrets
              key: JWT_SECRET_KEY
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: sentifinance-app-secrets
              key: SECRET_KEY
        - name: PORT
          value: "5000"
        - name: FLASK_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      imagePullSecrets:
      - name: acr-secret  # If using admin credentials
      # OR rely on AKS-ACR integration (recommended - no secret needed)
```

**Deploy:**

```bash
kubectl apply -f k8s/deployment.yaml

# Watch deployment progress
kubectl rollout status deployment/sentifinance-backend -n sentifinance

# Verify pods are running
kubectl get pods -n sentifinance -l app=sentifinance-backend

# Check pod logs
kubectl logs -n sentifinance -l app=sentifinance-backend --tail=50
```

---

### Step 7: Create Service (LoadBalancer)

**File: `k8s/service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sentifinance-backend
  namespace: sentifinance
  labels:
    app: sentifinance-backend
spec:
  type: LoadBalancer
  selector:
    app: sentifinance-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
    name: http
  sessionAffinity: None
```

**Deploy:**

```bash
kubectl apply -f k8s/service.yaml

# Wait for external IP (may take 2-3 minutes)
kubectl get service sentifinance-backend -n sentifinance --watch

# Once EXTERNAL-IP appears:
# NAME                    TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)
# sentifinance-backend    LoadBalancer   10.0.123.45    20.247.xxx.xxx   80:30123/TCP

# Test the endpoint
EXTERNAL_IP=$(kubectl get service sentifinance-backend -n sentifinance -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP/health
```

---

### Step 8: Configure Auto-Scaling

**File: `k8s/hpa.yaml`**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sentifinance-backend-hpa
  namespace: sentifinance
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sentifinance-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 2
        periodSeconds: 15
      selectPolicy: Max
```

**Deploy:**

```bash
kubectl apply -f k8s/hpa.yaml

# Verify HPA
kubectl get hpa -n sentifinance

# Check HPA details
kubectl describe hpa sentifinance-backend-hpa -n sentifinance
```

---

### Step 9: Configure Pod Disruption Budget

**File: `k8s/pdb.yaml`**

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: sentifinance-backend-pdb
  namespace: sentifinance
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: sentifinance-backend
```

**Deploy:**

```bash
kubectl apply -f k8s/pdb.yaml

# Verify PDB
kubectl get pdb -n sentifinance
```

---

## Complete Deployment Script

Create an automated deployment script:

**File: `scripts/deploy-k8s.sh`**

```bash
#!/bin/bash
set -e

echo "=== SentiFinance Kubernetes Deployment ==="

# Configuration
NAMESPACE="sentifinance"
RESOURCE_GROUP="sentifinance.azurecr.io"
AKS_CLUSTER="sentifinance-k8"

# Get AKS credentials
echo "📝 Getting AKS credentials..."
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER \
  --overwrite-existing

# Get Terraform outputs
echo "📝 Getting Terraform outputs..."
cd terraform/environments/production
ESO_CLIENT_ID=$(terraform output -raw eso_identity_client_id)
TENANT_ID=$(az account show --query tenantId -o tsv)
cd ../../..

echo "  ESO Client ID: $ESO_CLIENT_ID"
echo "  Tenant ID: $TENANT_ID"

# Create namespace
echo "📝 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Install ESO (if not installed)
if ! helm list -n external-secrets-operator | grep -q external-secrets; then
    echo "📝 Installing External Secrets Operator..."
    helm repo add external-secrets https://charts.external-secrets.io
    helm repo update
    helm install external-secrets \
      external-secrets/external-secrets \
      --namespace external-secrets-operator \
      --create-namespace \
      --set installCRDs=true

    echo "⏳ Waiting for ESO to be ready..."
    kubectl wait --for=condition=ready pod \
      -l app.kubernetes.io/name=external-secrets \
      -n external-secrets-operator \
      --timeout=180s
fi

# Create ServiceAccount
echo "📝 Creating ServiceAccount..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: external-secrets-sa
  namespace: $NAMESPACE
  annotations:
    azure.workload.identity/client-id: "$ESO_CLIENT_ID"
    azure.workload.identity/tenant-id: "$TENANT_ID"
EOF

# Deploy Kubernetes resources in order
echo "📝 Deploying SecretStore..."
kubectl apply -f k8s/secretstore.yaml

echo "📝 Deploying ExternalSecret..."
kubectl apply -f k8s/externalsecret.yaml

echo "⏳ Waiting for secret sync..."
sleep 10
kubectl wait --for=condition=Ready externalsecret/sentifinance-secrets \
  -n $NAMESPACE --timeout=60s

echo "📝 Deploying application..."
kubectl apply -f k8s/deployment.yaml

echo "📝 Creating service..."
kubectl apply -f k8s/service.yaml

echo "📝 Configuring HPA..."
kubectl apply -f k8s/hpa.yaml

echo "📝 Configuring PDB..."
kubectl apply -f k8s/pdb.yaml

echo "⏳ Waiting for deployment..."
kubectl rollout status deployment/sentifinance-backend -n $NAMESPACE --timeout=300s

echo ""
echo "=== Deployment Complete ==="
echo ""
kubectl get all -n $NAMESPACE

echo ""
echo "📝 Getting LoadBalancer IP..."
kubectl get service sentifinance-backend -n $NAMESPACE

echo ""
echo "✅ Deployment successful!"
echo ""
echo "Next steps:"
echo "  1. Wait for EXTERNAL-IP to be assigned"
echo "  2. Test endpoint: curl http://<EXTERNAL-IP>/health"
echo "  3. Monitor logs: kubectl logs -n $NAMESPACE -l app=sentifinance-backend"
```

**Run the deployment:**

```bash
chmod +x scripts/deploy-k8s.sh
./scripts/deploy-k8s.sh
```

---

## Verification Checklist

After deployment, verify everything is working:

```bash
# 1. Check all pods are running
kubectl get pods -n sentifinance

# 2. Check service has external IP
kubectl get svc -n sentifinance

# 3. Check secrets are synced
kubectl get secret sentifinance-app-secrets -n sentifinance

# 4. Check HPA is active
kubectl get hpa -n sentifinance

# 5. Test health endpoint
EXTERNAL_IP=$(kubectl get svc sentifinance-backend -n sentifinance -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP/health

# 6. Check application logs
kubectl logs -n sentifinance -l app=sentifinance-backend --tail=100

# 7. Test database connection
kubectl exec -n sentifinance -it deployment/sentifinance-backend -- \
  python -c "import os; print('DB:', os.getenv('DATABASE_URI')[:30]+'...')"
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n sentifinance

# Describe pod to see events
kubectl describe pod <pod-name> -n sentifinance

# Check logs
kubectl logs <pod-name> -n sentifinance

# Common issues:
# - Image pull errors: Check ACR integration
# - Secret not found: Check ExternalSecret synced
# - Database connection: Check DATABASE_URI secret
```

### Secret Not Syncing

```bash
# Check ExternalSecret status
kubectl describe externalsecret sentifinance-secrets -n sentifinance

# Check SecretStore
kubectl describe secretstore azure-secret-store -n sentifinance

# Check ESO logs
kubectl logs -n external-secrets-operator -l app.kubernetes.io/name=external-secrets

# Verify workload identity
kubectl describe sa external-secrets-sa -n sentifinance
```

### Service No External IP

```bash
# Check service status
kubectl describe svc sentifinance-backend -n sentifinance

# Check for errors in events

# Manually check LoadBalancer
az network lb list --resource-group MC_*_sentifinance-k8_* -o table

# If stuck, recreate service
kubectl delete svc sentifinance-backend -n sentifinance
kubectl apply -f k8s/service.yaml
```

---

## Updating the Application

### Update Image

```bash
# 1. Build and push new image (via CI/CD)
# 2. Update deployment
kubectl set image deployment/sentifinance-backend \
  backend=sentifinancetwo.azurecr.io/sentifinance-backend:v2.0.0 \
  -n sentifinance

# 3. Watch rollout
kubectl rollout status deployment/sentifinance-backend -n sentifinance

# 4. Rollback if needed
kubectl rollout undo deployment/sentifinance-backend -n sentifinance
```

### Update Environment Variables

```bash
# Edit deployment
kubectl edit deployment sentifinance-backend -n sentifinance

# Or apply updated YAML
kubectl apply -f k8s/deployment.yaml
```

---

## Clean Up

To remove all resources:

```bash
# Delete all resources in namespace
kubectl delete namespace sentifinance

# Uninstall ESO (if needed)
helm uninstall external-secrets -n external-secrets-operator
kubectl delete namespace external-secrets-operator
```

---

## Next Steps

1. ✅ All Kubernetes resources deployed
2. ✅ Application is running
3. ✅ LoadBalancer is exposing service
4. 📝 Set up monitoring (Prometheus/Grafana)
5. 📝 Configure alerts
6. 📝 Set up CI/CD pipeline for automated deployments

---

**Created:** 2025-11-22
**Last Updated:** 2025-11-22
**Maintained By:** DevOps Team
