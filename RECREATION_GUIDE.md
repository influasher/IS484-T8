# Complete Infrastructure Recreation Guide

This is the **master guide** for recreating the entire SentiFinance infrastructure from scratch. Follow these steps in order for a complete deployment.
## 📋 Overview

This guide will help you recreate:
- ✅ All Azure infrastructure (AKS, ACR, VNet, Storage, Key Vault, Managed Identities)
- ✅ PostgreSQL database
- ✅ Application secrets in Key Vault
- ✅ Kubernetes resources and application deployment
- ✅ CI/CD pipeline configuration

**Estimated Time:** 2-3 hours for complete setup

---

## 🔧 Prerequisites

### Required Tools

```bash
# 1. Azure CLI
az version  # Should be >= 2.50.0
# Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# 2. Terraform
terraform version  # Should be >= 1.5.0
# Install: https://www.terraform.io/downloads

# 3. kubectl
kubectl version --client  # Should be >= 1.28.0
# Install: https://kubernetes.io/docs/tasks/tools/

# 4. Helm
helm version  # Should be >= 3.12.0
# Install: https://helm.sh/docs/intro/install/

# 5. GitHub CLI (optional, for CI/CD)
gh version
# Install: https://cli.github.com/
```

### Required Access

- Azure subscription with Owner or Contributor role
- (Optional) Separate Azure subscription for PostgreSQL database
- GitHub repository access (for CI/CD setup)

### Repository Setup

```bash
# Clone repository
git clone <repository-url>
cd IS484-T8

# Verify structure
ls -la terraform/
ls -la k8s/
ls -la Backend/
```

---

## 📅 Phase 1: Azure Infrastructure (Terraform)

### Step 1.1: Setup Remote State Storage

```bash
# Set variables
export TF_STATE_RESOURCE_GROUP="sentifinance-terraform-rg"
export TF_STATE_STORAGE_ACCOUNT="sentifinancetfstate$(date +%s | tail -c 5)"
export TF_STATE_CONTAINER="tfstate"
export LOCATION="southeastasia"

# Create resource group
az group create \
  --name $TF_STATE_RESOURCE_GROUP \
  --location $LOCATION

# Create storage account
az storage account create \
  --resource-group $TF_STATE_RESOURCE_GROUP \
  --name $TF_STATE_STORAGE_ACCOUNT \
  --sku Standard_LRS \
  --encryption-services blob \
  --https-only true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# Create container
az storage container create \
  --name $TF_STATE_CONTAINER \
  --account-name $TF_STATE_STORAGE_ACCOUNT \
  --auth-mode login

# Enable versioning
az storage account blob-service-properties update \
  --resource-group $TF_STATE_RESOURCE_GROUP \
  --account-name $TF_STATE_STORAGE_ACCOUNT \
  --enable-versioning true

# Get storage account key
STORAGE_ACCOUNT_KEY=$(az storage account keys list \
  --resource-group $TF_STATE_RESOURCE_GROUP \
  --account-name $TF_STATE_STORAGE_ACCOUNT \
  --query '[0].value' -o tsv)

echo "Storage Account Name: $TF_STATE_STORAGE_ACCOUNT"
echo "Storage Account Key: $STORAGE_ACCOUNT_KEY"

# Save for later
export ARM_ACCESS_KEY="$STORAGE_ACCOUNT_KEY"
```

### Step 1.2: Configure Terraform Backend

```bash
cd terraform/environments/production

# Update backend.tf with your storage account name
sed -i '' "s/REPLACE_WITH_YOUR_STORAGE_ACCOUNT/$TF_STATE_STORAGE_ACCOUNT/" backend.tf

# Create terraform.tfvars from example
cp terraform.tfvars.example terraform.tfvars

# Review and update values if needed (defaults should work)
cat terraform.tfvars
```

### Step 1.3: Initialize and Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates ~17 resources)
terraform apply

# Expected resources:
# - Resource Group
# - Virtual Network + 3 Subnets
# - Storage Account
# - Container Registry (ACR)
# - AKS Cluster
# - Key Vault
# - 2 Managed Identities
# - Application Gateway for Containers
# - Role Assignments

# Save outputs
terraform output > ../../../terraform-outputs.txt
```

**⏱️ Duration:** ~15-20 minutes

---

## 📅 Phase 2: PostgreSQL Database

### Step 2.1: Create PostgreSQL Server

Choose **Option A** (same subscription) or **Option B** (separate subscription):

#### Option A: Same Subscription (Recommended)

```bash
cd terraform/environments/production

# 1. Uncomment PostgreSQL module in main.tf
# Edit main.tf lines 181-199 to uncomment the module

# 2. Add password variable to terraform.tfvars
echo 'postgresql_admin_password = "ChangeMe123!Secure"' >> terraform.tfvars

# 3. Apply Terraform
terraform apply

# 4. Get connection details
terraform output postgresql_fqdn
```

#### Option B: Separate Subscription

See [terraform/POSTGRESQL_SETUP.md](terraform/POSTGRESQL_SETUP.md) for detailed instructions.

### Step 2.2: Run Database Migrations

```bash
# Get connection string
PGHOST=$(terraform output -raw postgresql_fqdn)
PGUSER="sentiadmin"
PGPASSWORD="ChangeMe123!Secure"
PGDATABASE="postgres"

# Connect and verify
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "SELECT version();"

# Run migrations (if you have migration scripts)
cd ../../Backend
# Using Alembic:
# alembic upgrade head
# Or using SQL scripts:
# psql -h $PGHOST -U $PGUSER -d $PGDATABASE -f schema.sql
```

**⏱️ Duration:** ~5-10 minutes

---

## 📅 Phase 3: Application Secrets

### Step 3.1: Populate Key Vault

```bash
# Run automated setup script
./scripts/setup-secrets.sh

# Or manual setup:
# See terraform/SECRETS_SETUP.md for detailed instructions
```

**The script will prompt for:**
- PostgreSQL hostname
- PostgreSQL username
- PostgreSQL password
- Database name

**It will automatically generate:**
- JWT_SECRET_KEY (random 64-char string)
- SECRET_KEY (random 64-char string)

### Step 3.2: Verify Secrets

```bash
# List secrets
az keyvault secret list \
  --vault-name sentifinance-key-vault \
  --query "[].name" -o tsv

# Expected output:
# DATABASE-URI
# JWT-SECRET-KEY
# SECRET-KEY
```

**⏱️ Duration:** ~5 minutes

---

## 📅 Phase 4: Kubernetes Deployment

### Step 4.1: Get AKS Credentials

```bash
# Get cluster credentials
az aks get-credentials \
  --resource-group sentifinance.azurecr.io \
  --name sentifinance-k8 \
  --overwrite-existing

# Verify connection
kubectl get nodes
```

### Step 4.2: Deploy Application

```bash
# Run automated deployment script
./scripts/deploy-k8s.sh

# Or manual deployment:
# See terraform/K8S_MANIFESTS_GUIDE.md for step-by-step instructions
```

**The script will:**
1. Create namespace
2. Install External Secrets Operator
3. Configure workload identity
4. Create SecretStore and ExternalSecret
5. Deploy application
6. Create LoadBalancer service
7. Configure HPA and PDB

### Step 4.3: Verify Deployment

```bash
# Check all resources
kubectl get all -n sentifinance

# Wait for LoadBalancer IP
kubectl get svc sentifinance-backend -n sentifinance --watch

# Test application
EXTERNAL_IP=$(kubectl get svc sentifinance-backend -n sentifinance -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP/health

# Expected: {"status": "healthy"}
```

**⏱️ Duration:** ~10-15 minutes

---

## 📅 Phase 5: CI/CD Pipeline Setup

### Step 5.1: Configure GitHub Secrets

```bash
# Get service principal credentials
SP_CREDS=$(az ad sp create-for-rbac \
  --name "github-actions-sentifinance" \
  --role "Contributor" \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/sentifinance.azurecr.io \
  --sdk-auth)

# Set GitHub secrets
gh secret set AZURE_CREDENTIALS --body "$SP_CREDS"
gh secret set ARM_ACCESS_KEY --body "$ARM_ACCESS_KEY"
gh secret set ACR_LOGIN_SERVER --body "sentifinancetwo.azurecr.io"
gh secret set ACR_USERNAME --body "sentifinancetwo"

# Get ACR password
ACR_PASSWORD=$(az acr credential show \
  --name sentifinancetwo \
  --query "passwords[0].value" -o tsv)

gh secret set ACR_PASSWORD --body "$ACR_PASSWORD"

# List secrets
gh secret list
```

### Step 5.2: Test CI/CD Pipeline

```bash
# Trigger workflow
git commit --allow-empty -m "test: trigger CI/CD pipeline"
git push origin main

# Watch workflow
gh run watch
```

**⏱️ Duration:** ~5-10 minutes

---

## 📅 Phase 6: Verification & Testing

### Step 6.1: Infrastructure Verification

```bash
# Check Terraform state
cd terraform/environments/production
terraform state list | wc -l  # Should show ~17 resources

# Verify all Azure resources
az resource list --resource-group sentifinance.azurecr.io --output table

# Check costs
az consumption usage list \
  --start-date $(date -u -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date -u +%Y-%m-%d) \
  --query "[?contains(instanceName, 'sentifinance')].{Name:instanceName, Cost:pretaxCost}" \
  --output table
```

### Step 6.2: Application Health Checks

```bash
# Check pod health
kubectl get pods -n sentifinance

# Check application logs
kubectl logs -n sentifinance -l app=sentifinance-backend --tail=100

# Test all endpoints
EXTERNAL_IP=$(kubectl get svc sentifinance-backend -n sentifinance -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Health check
curl http://$EXTERNAL_IP/health

# API test (example)
curl -X POST http://$EXTERNAL_IP/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Step 6.3: Security Verification

```bash
# Check secret sync
kubectl get secret sentifinance-app-secrets -n sentifinance

# Verify workload identity
kubectl describe sa external-secrets-sa -n sentifinance

# Check network policies
kubectl get networkpolicy -n sentifinance

# Verify RBAC
kubectl auth can-i --list --namespace=sentifinance
```

**⏱️ Duration:** ~10 minutes

---

## 📊 Post-Deployment Checklist

- [ ] All Terraform resources created (~17 resources)
- [ ] PostgreSQL database accessible
- [ ] 3 secrets in Key Vault (DATABASE-URI, JWT-SECRET-KEY, SECRET-KEY)
- [ ] AKS cluster running with 4 nodes
- [ ] Application pods running (3+ replicas)
- [ ] LoadBalancer has external IP
- [ ] Health endpoint returns 200
- [ ] CI/CD pipeline executes successfully
- [ ] Monitoring dashboard accessible
- [ ] Logs flowing to Log Analytics
- [ ] Cost alerts configured

---

## 📚 Documentation Reference

| Guide | Purpose |
|-------|---------|
| [terraform/README.md](terraform/README.md) | Terraform usage and module documentation |
| [terraform/INFRASTRUCTURE_SUMMARY.md](terraform/INFRASTRUCTURE_SUMMARY.md) | Quick reference for all resources |
| [terraform/TERRAFORM_IMPORT_GUIDE.md](terraform/TERRAFORM_IMPORT_GUIDE.md) | Import existing infrastructure |
| [terraform/POSTGRESQL_SETUP.md](terraform/POSTGRESQL_SETUP.md) | PostgreSQL database setup |
| [terraform/SECRETS_SETUP.md](terraform/SECRETS_SETUP.md) | Key Vault secrets configuration |
| [terraform/K8S_MANIFESTS_GUIDE.md](terraform/K8S_MANIFESTS_GUIDE.md) | Kubernetes deployment |
| [INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md) | Operations and maintenance |

---

## 🚨 Troubleshooting

### Terraform Apply Fails

```bash
# Check Azure login
az account show

# Verify permissions
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv)

# Check Terraform state
terraform state list

# Common fixes:
terraform init -upgrade
terraform plan -refresh-only
```

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n sentifinance

# Common issues:
# 1. Image pull errors - check ACR integration
# 2. Secret not found - check ExternalSecret synced
# 3. Database connection - verify DATABASE_URI

# Force secret refresh
kubectl delete externalsecret sentifinance-secrets -n sentifinance
kubectl apply -f k8s/externalsecret.yaml
```

### LoadBalancer No IP

```bash
# Check service
kubectl describe svc sentifinance-backend -n sentifinance

# Delete and recreate
kubectl delete svc sentifinance-backend -n sentifinance
kubectl apply -f k8s/service.yaml

# Check Azure LoadBalancer
az network lb list --resource-group MC_* -o table
```

---

## 💰 Cost Estimates

**Monthly Costs (Production):**

| Resource | Cost (USD) |
|----------|-----------|
| AKS (4 x D2lds_v6 nodes) | ~$120 |
| ACR Standard | ~$5 |
| Storage Account (RAGRS) | ~$25 |
| Key Vault | ~$1 |
| App Gateway for Containers | ~$30 |
| PostgreSQL (B_Standard_B1ms) | ~$15 |
| **Total** | **~$196/month** |

**To reduce costs:**
- Stop AKS cluster when not in use: `az aks stop --name sentifinance-k8 --resource-group sentifinance.azurecr.io`
- Use spot instances for development
- Reduce node count to 2 for non-production

---

## 🎯 Success Criteria

Your infrastructure is **fully operational** when:

1. ✅ `terraform plan` shows no changes
2. ✅ All pods are Running: `kubectl get pods -n sentifinance`
3. ✅ Health endpoint returns 200: `curl http://<EXTERNAL-IP>/health`
4. ✅ Can query database: `kubectl exec -n sentifinance deployment/sentifinance-backend -- python -c "import os; print(os.getenv('DATABASE_URI')[:20])"`
5. ✅ CI/CD pipeline passes
6. ✅ Auto-scaling works: `kubectl get hpa -n sentifinance`

---

## 🔄 Next Steps

After successful recreation:

1. **Configure Monitoring**
   - Set up Prometheus/Grafana dashboards
   - Configure alerts for pod failures, high CPU, etc.

2. **Security Hardening**
   - Enable Azure Policy
   - Configure Network Policies in Kubernetes
   - Set up Web Application Firewall

3. **Performance Tuning**
   - Load testing
   - Database query optimization
   - Cache layer (Redis)

4. **Backup Strategy**
   - Automated database backups
   - Terraform state backups
   - Disaster recovery plan

---

**Created:** 2025-11-22
**Last Updated:** 2025-11-22
**Version:** 1.0
**Maintained By:** DevOps Team

**Questions?** Refer to individual guides linked above or contact the DevOps team.
