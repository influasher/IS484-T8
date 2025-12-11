# Infrastructure Summary for Handover

This document provides a quick reference for all Azure resources managed (and not managed) by Terraform.

## Quick Facts

- **Environment:** Production
- **Azure Subscription:** Main subscription (sentifinance.azurecr.io resource group)
- **Location:** Primary: Southeast Asia, Secondary: East US (storage), East Asia (ACR)
- **Terraform State:** Azure Storage Account (remote backend with versioning)
- **Total Resources Managed:** ~17 resources
- **PostgreSQL:** In SEPARATE subscription (not managed by Terraform)

## Resource Inventory

### Managed by Terraform

| Resource Type | Name | Location | Purpose |
|---------------|------|----------|---------|
| **Resource Group** | sentifinance.azurecr.io | southeastasia | Container for all resources |
| **Virtual Network** | sentifinance.azurecr.io-vnet | southeastasia | Network for AKS, App Gateway |
| - Subnet (default) | 10.224.0.0/16 | - | AKS nodes |
| - Subnet (virtual-node-aci) | 10.239.0.0/16 | - | Azure Container Instances |
| - Subnet (ingress-appgateway-subnet) | 10.225.0.0/16 | - | Application Gateway |
| **Storage Account** | sentifinanceblob | eastus | General purpose storage (RAGRS) |
| **Container Registry** | sentifinancetwo | eastasia | Docker images |
| **AKS Cluster** | sentifinance-k8 | southeastasia | Kubernetes cluster |
| - Kubernetes Version | 1.32.7 | - | Latest version |
| - Node Pool | agentpool | - | 4 nodes (autoscale 3-5) |
| - VM Size | Standard_D2lds_v6 | - | 2 vCPU, 4GB RAM |
| - Network Plugin | Azure CNI | - | Advanced networking |
| - Availability Zones | 2, 3 | - | High availability |
| **Key Vault** | sentifinance-key-vault | southeastasia | Secrets management |
| **Managed Identity** | sentifinance-secrets-identity | southeastasia | ESO workload identity |
| **Managed Identity** | ua-id-ba65 | southeastasia | Additional identity |
| **App Gateway (Containers)** | sentifinance-app-gateway | southeastasia | Traffic controller |

### NOT Managed by Terraform

| Resource Type | Name | Reason |
|---------------|------|--------|
| **PostgreSQL Flexible Server** | psql-sentifinance-dev | In separate subscription |
| **Grafana Dashboard** | grafana-20251013132532 | Auto-created by AKS monitoring |
| **Log Analytics** | 2 workspaces | Auto-created by AKS monitoring |
| **Azure Monitor** | defaultazuremonitorworkspace-sea | Auto-created by AKS monitoring |
| **Prometheus Rules** | 6 rule groups | Auto-created by AKS monitoring |
| **Metric Alerts** | CPU, Memory alerts | Auto-created by AKS monitoring |
| **ACR Webhook** | webappsentifinancetwo | Legacy resource |

## Network Architecture

```
VNet: sentifinance.azurecr.io-vnet (10.224.0.0/12)
│
├─ Subnet: default (10.224.0.0/16)
│  └─ AKS Node Pool (4 nodes, zones 2-3)
│     ├─ Pod Network (Azure CNI)
│     ├─ Service CIDR: 10.0.0.0/16
│     └─ DNS: 10.0.0.10
│
├─ Subnet: virtual-node-aci (10.239.0.0/16)
│  └─ Azure Container Instances (VCI)
│
└─ Subnet: ingress-appgateway-subnet (10.225.0.0/16)
   └─ Application Gateway for Containers
```

## Critical Configuration Details

### AKS Cluster
- **Network Plugin:** Azure CNI (NOT kubenet)
- **Node Pool Name:** agentpool (NOT default)
- **Autoscaling:** Enabled (min: 3, max: 5, current: 4)
- **OIDC Issuer:** Enabled (for workload identity)
- **Workload Identity:** Enabled (ESO uses this)
- **ACR Integration:** AcrPull role assignment

### External Secrets Operator (ESO)
- **Managed Identity:** sentifinance-secrets-identity
- **Workload Identity:** Enabled with federated credential
- **Key Vault Access:** "Key Vault Secrets User" role
- **Kubernetes SA:** external-secrets-sa in sentifinance namespace

### PostgreSQL Database (Separate Subscription)
- **Connection String:** Stored in Azure Key Vault
- **Format:** `postgresql+psycopg2://user:password@psql-sentifinance-dev.postgres.database.azure.com:5432/postgres`
- **Access:** Via Key Vault secret (DATABASE_URI)

### Storage Account
- **Replication:** RAGRS (Read-Access Geo-Redundant)
- **Location:** East US (different from other resources)
- **Access Tier:** Hot
- **HTTPS Only:** Yes
- **Min TLS:** 1.2

## GitHub Secrets

Required secrets for CI/CD:

| Secret Name | Purpose |
|-------------|---------|
| ARM_ACCESS_KEY | Terraform remote state access |
| AZURE_CREDENTIALS | Azure service principal for deployments |
| DATABASE_URI | PostgreSQL connection string |
| JWT_SECRET_KEY | Application JWT secret |
| SECRET_KEY | Application secret key |

## Cost Estimate

Approximate monthly costs:

| Resource | Cost (USD/month) |
|----------|------------------|
| AKS Cluster (4 x D2lds_v6) | ~$120 |
| ACR Standard | ~$5 |
| Storage Account RAGRS | ~$25 |
| Key Vault | ~$1 |
| App Gateway for Containers | ~$30 |
| **Total (this subscription)** | **~$181** |

*PostgreSQL costs are in separate subscription*

## Disaster Recovery

### Terraform State Backup
- **Backend:** Azure Storage Account
- **Versioning:** Enabled
- **Soft Delete:** 30 days retention
- **Backup:** Automatic via storage account versioning

### Database Backup
- **PostgreSQL:** In separate subscription
- **Backup Retention:** Check with DB admin
- **Connection String:** Stored in Key Vault

### Container Images
- **ACR:** sentifinancetwo.azurecr.io
- **Retention:** Manual (no auto-deletion)
- **Backup:** Images can be pulled and pushed to different registry

## Important Notes for Handover

1. **PostgreSQL is NOT in this Terraform**
   - Located in different subscription
   - Must be managed separately
   - Connection string in Key Vault

2. **Monitoring Resources are Auto-Created**
   - Grafana, Prometheus, Log Analytics
   - Created automatically by AKS
   - Do NOT delete manually
   - Do NOT try to import into Terraform

3. **ACR Name is "sentifinancetwo" not "sentifinance"**
   - Important for CI/CD pipelines
   - Update any scripts that reference "sentifinance"

4. **AKS Uses Azure CNI**
   - NOT kubenet
   - Each pod gets IP from VNet
   - More IP addresses consumed
   - Better performance and features

5. **Workload Identity is Enabled**
   - ESO uses workload identity (not pod identity)
   - Requires federated credential
   - More secure than managed identity injection

## Quick Start Guide

### Access the Infrastructure

```bash
# Login to Azure
az login
az account set --subscription "59160e64-fc6d-4a3b-94fc-d2563d9d1d80"

# Get AKS credentials
az aks get-credentials --resource-group sentifinance.azurecr.io --name sentifinance-k8

# Verify access
kubectl get nodes
kubectl get pods -n sentifinance
```

### Make Infrastructure Changes

```bash
# Navigate to Terraform
cd terraform/environments/production

# Set remote state access
export ARM_ACCESS_KEY="<storage-account-key>"

# Initialize Terraform
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply
```

### Check Resource Status

```bash
# AKS cluster
az aks show --resource-group sentifinance.azurecr.io --name sentifinance-k8

# ACR
az acr repository list --name sentifinancetwo

# Key Vault secrets
az keyvault secret list --vault-name sentifinance-key-vault

# Storage account
az storage account show --name sentifinanceblob --resource-group sentifinance.azurecr.io
```

## Troubleshooting Common Issues

### Terraform Plan Shows Many Changes After Import

**Cause:** Configuration doesn't match reality
**Fix:** Update `terraform.tfvars` with actual values from Azure Portal

### Cannot Access Key Vault

**Cause:** Missing access policy
**Fix:** Add access policy via Azure Portal or Terraform

### ESO Cannot Read Secrets

**Cause:** Workload identity or role assignment issue
**Fix:** Verify federated credential and "Key Vault Secrets User" role

### AKS Nodes Not Scaling

**Cause:** Autoscaler configuration or resource limits
**Fix:** Check AKS autoscaler logs and node pool settings

## Documentation Links

- [Terraform README](README.md) - Complete Terraform documentation
- [Terraform Import Guide](TERRAFORM_IMPORT_GUIDE.md) - Step-by-step import instructions
- [Infrastructure Guide](../INFRASTRUCTURE_GUIDE.md) - Operational guide
- [Azure Portal](https://portal.azure.com) - View resources visually

---

**Created:** 2025-11-22
**Last Updated:** 2025-11-22
**Maintained By:** DevOps Team
**Questions:** Contact team lead or refer to documentation above
