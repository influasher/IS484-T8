# Kubernetes Deployment for SentiFinance

This directory contains Kubernetes manifests for deploying SentiFinance to Azure Kubernetes Service (AKS).

## Files Overview

- **`deployment.yaml`** - Main application deployment with 2 replicas
- **`service.yaml`** - LoadBalancer service to expose the app
- **`configmap.yaml`** - Non-sensitive configuration
- **`secrets-template.yaml`** - Template for sensitive data (DO NOT commit real secrets)
- **`hpa.yaml`** - Horizontal Pod Autoscaler for automatic scaling
- **`namespace.yaml`** - Dedicated namespace (optional)
- **`ingress.yaml`** - Custom domain configuration (optional)
- **`kustomization.yaml`** - Kustomize configuration for organized deployment

## Prerequisites

1. **AKS Cluster**: Create an AKS cluster in Azure
2. **ACR Integration**: Attach your ACR to the AKS cluster
3. **kubectl**: Install and configure kubectl
4. **Secrets**: Create the required secrets (see below)

## Setup Instructions

### 1. Create AKS Cluster (if not exists)
```bash
az aks create \
  --resource-group sentifinance2 \
  --name sentifinance-aks \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --attach-acr sentifinancetwo \
  --generate-ssh-keys
```

### 2. Get AKS Credentials
```bash
az aks get-credentials \
  --resource-group sentifinance2 \
  --name sentifinance-aks \
  --overwrite-existing
```

### 3. Create Secrets
```bash
kubectl create secret generic sentifinance-secrets \
  --from-literal=secret-key="your-production-secret-key-here" \
  --from-literal=database-uri="sqlite:///production.db" \
  --from-literal=jwt-secret-key="your-production-jwt-secret-here"
```

### 4. Deploy Application
```bash
# Apply all manifests
kubectl apply -f k8s/

# OR use kustomize
kubectl apply -k k8s/
```

### 5. Check Deployment Status
```bash
# Check pods
kubectl get pods -n sentifinance

# Check services
kubectl get services -n sentifinance

# Check deployment status
kubectl rollout status deployment/sentifinance-backend -n sentifinance
```

### 6. Get External IP
```bash
kubectl get service sentifinance-service -n sentifinance
# Wait for EXTERNAL-IP to be assigned
```

## Required GitHub Secrets

Add these secrets to your GitHub repository for the CD pipeline:

```
AKS_CLUSTER_NAME=sentifinance-aks
AKS_RESOURCE_GROUP=sentifinance2
AKS_LOADBALANCER_IP=<external-ip-from-step-6>
```

## Scaling

The HPA (Horizontal Pod Autoscaler) will automatically scale pods based on:
- CPU usage > 70%
- Memory usage > 80%
- Min replicas: 2
- Max replicas: 10

## Monitoring

```bash
# Watch pods
kubectl get pods -n sentifinance -w

# Check logs
kubectl logs -f deployment/sentifinance-backend -n sentifinance

# Describe deployment
kubectl describe deployment sentifinance-backend -n sentifinance
```

## Troubleshooting

### Image Pull Issues
```bash
# Check if ACR is attached
az aks show --resource-group sentifinance2 --name sentifinance-aks --query addonProfiles.acrProfile

# Manually attach ACR if needed
az aks update --resource-group sentifinance2 --name sentifinance-aks --attach-acr sentifinancetwo
```

### Pod Startup Issues
```bash
# Check pod events
kubectl describe pod <pod-name> -n sentifinance

# Check application logs
kubectl logs <pod-name> -n sentifinance
```