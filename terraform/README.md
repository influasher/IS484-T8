# SentiFinance Infrastructure as Code

This directory contains Terraform configurations for managing the SentiFinance infrastructure on Azure.

## 📋 Overview

**Current Architecture:**
- LoadBalancer Service exposing application on HTTP
- 2-replica deployment for high availability
- External Secrets Operator syncing from Azure Key Vault
- Database migrations via Kubernetes Job
- Automatic rollback on deployment failures

**Terraform manages:**
- Resource Group
- Azure Kubernetes Service (AKS) cluster
- Azure Container Registry (ACR)
- Azure Key Vault
- Azure PostgreSQL Flexible Server
- Managed Identities & Role Assignments

**State storage:** Azure Storage Account (remote backend with versioning)

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install Terraform (macOS)
brew install terraform

# Install Azure CLI
brew install azure-cli

# Login to Azure
az login
az account set --subscription "<your-subscription-id>"
```

### First-Time Setup

```bash
# 1. Navigate to production environment
cd terraform/environments/production

# 2. Copy example variables
cp terraform.tfvars.example terraform.tfvars

# 3. Edit terraform.tfvars with your actual values
# (This file is gitignored)

# 4. Create remote state storage (see "Setup Remote State" section below)

# 5. Update backend.tf with your storage account name

# 6. Set ARM_ACCESS_KEY environment variable
export ARM_ACCESS_KEY="<your-storage-account-key>"

# 7. Initialize Terraform
terraform init

# 8. Review what Terraform will manage
terraform plan

# 9. If plan looks good (should show no changes if imports were correct)
terraform apply
```

---

## 🔧 Setup Remote State Storage

Before using Terraform, you need to create Azure Storage for the remote state:

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

# Save key to GitHub Secrets
gh secret set ARM_ACCESS_KEY --body "$STORAGE_ACCOUNT_KEY"

# Update backend.tf with storage account name
# Then you can run: terraform init
```

---

## 📂 Directory Structure

```
terraform/
├── environments/
│   └── production/
│       ├── main.tf                    # Root module & provider config
│       ├── variables.tf               # Input variables
│       ├── outputs.tf                 # Output values
│       ├── backend.tf                 # Remote state configuration
│       ├── terraform.tfvars.example   # Example variable values
│       ├── terraform.tfvars           # Actual values (gitignored)
│       ├── resource-inventory.json    # Current resource snapshot
│       └── resource-ids.sh            # Resource IDs for import
├── modules/
│   ├── aks/                           # AKS cluster module
│   ├── acr/                           # Container registry module
│   ├── keyvault/                      # Key Vault module
│   └── postgresql/                    # PostgreSQL server module
├── scripts/
│   └── inventory-resources.sh         # Resource inventory script
└── README.md                           # This file
```

---

## 📦 Importing Existing Infrastructure

If you're setting up Terraform for the first time with existing infrastructure:

### Step 1: Inventory Your Resources

```bash
# Run inventory script (from repo root)
chmod +x terraform/scripts/inventory-resources.sh
./terraform/scripts/inventory-resources.sh "sentifinance.azurecr.io"

# Load resource IDs
cd terraform/environments/production
source resource-ids.sh

# Verify IDs are loaded
echo "Resource Group: $RG_ID"
echo "AKS: $AKS_ID"
echo "ACR: $ACR_ID"
echo "Key Vault: $KV_ID"
echo "PostgreSQL: $PSQL_ID"
```

### Step 2: Initialize Terraform

```bash
cd terraform/environments/production

# Make sure backend.tf has your storage account name
# Make sure ARM_ACCESS_KEY is set
export ARM_ACCESS_KEY="<your-key>"

terraform init
```

### Step 3: Import Resources

```bash
# Import Resource Group
terraform import azurerm_resource_group.main "$RG_ID"

# Import ACR
terraform import module.acr.azurerm_container_registry.this "$ACR_ID"

# Import AKS
terraform import module.aks.azurerm_kubernetes_cluster.this "$AKS_ID"

# Import Key Vault
terraform import module.keyvault.azurerm_key_vault.this "$KV_ID"

# Import PostgreSQL
terraform import module.postgresql.azurerm_postgresql_flexible_server.this "$PSQL_ID"

# Import PostgreSQL Database (get DB ID first)
PSQL_DB_ID=$(az postgres flexible-server db show \
  --resource-group sentifinance.azurecr.io \
  --server-name psql-sentifinance-dev \
  --database-name postgres \
  --query id -o tsv)
terraform import module.postgresql.azurerm_postgresql_flexible_server_database.this "$PSQL_DB_ID"

# Import PostgreSQL Firewall Rule (get rule ID)
PSQL_FW_ID=$(az postgres flexible-server firewall-rule show \
  --resource-group sentifinance.azurecr.io \
  --server-name psql-sentifinance-dev \
  --rule-name AllowAzureServices \
  --query id -o tsv)
terraform import module.postgresql.azurerm_postgresql_flexible_server_firewall_rule.azure_services "$PSQL_FW_ID"
```

### Step 4: Align Configuration with Reality

```bash
# Run plan to see differences
terraform plan

# You'll likely see differences - update your Terraform config to match reality
# Check actual AKS configuration
az aks show --resource-group sentifinance.azurecr.io --name sentifinance-k8 --output json > aks-actual.json

# Update variables in terraform.tfvars or module configs to match actual values
```

---

## 🛠️ Common Operations

### View Current State

```bash
cd terraform/environments/production

# List all managed resources
terraform state list

# Show specific resource details
terraform state show module.aks.azurerm_kubernetes_cluster.this

# View outputs
terraform output

# Get specific output
terraform output acr_login_server
```

### Plan Changes

```bash
# Preview changes before applying
terraform plan

# Save plan to file for review
terraform plan -out=tfplan

# Review saved plan
terraform show tfplan
```

### Apply Changes

```bash
# Apply changes (with confirmation prompt)
terraform apply

# Apply saved plan (no prompt)
terraform apply tfplan

# Apply with auto-approve (use carefully!)
terraform apply -auto-approve
```

### Refresh State

```bash
# Update state to match real infrastructure
terraform apply -refresh-only

# Just refresh, don't apply
terraform plan -refresh-only
```

### Format and Validate

```bash
# Format all Terraform files
terraform fmt -recursive

# Validate configuration
terraform validate
```

---

## 🔐 Security Best Practices

### Secrets Management

1. **Never commit sensitive values:**
   - `terraform.tfvars` is gitignored
   - Use Azure Key Vault for application secrets
   - Reference via data sources when needed

2. **Protect Terraform state:**
   - Remote state in Azure Storage
   - Encryption at rest enabled
   - Versioning enabled for rollback
   - Access key stored in GitHub Secrets / Key Vault

3. **Use managed identities:**
   - AKS uses system-assigned identity
   - Workload identity for pods (ESO)

### Access Control

```bash
# View state storage access
az storage account show \
  --name <storage-account> \
  --query "networkAcls"

# Lock down state storage (recommended for production)
az storage account update \
  --name <storage-account> \
  --default-action Deny \
  --bypass AzureServices
```

### State File Protection

```bash
# Enable soft delete on storage account
az storage account blob-service-properties delete-policy update \
  --account-name <storage-account> \
  --enable true \
  --days-retained 30

# List state versions (rollback capability)
az storage blob list \
  --account-name <storage-account> \
  --container-name tfstate \
  --query "[].{Name:name, LastModified:properties.lastModified}" -o table
```

---

## 📊 Outputs Reference

After running `terraform apply`, these outputs are available:

| Output | Description | Usage |
|--------|-------------|-------|
| `aks_cluster_name` | AKS cluster name | Reference in scripts |
| `aks_cluster_id` | AKS cluster ID | RBAC assignments |
| `aks_oidc_issuer_url` | OIDC issuer for workload identity | ESO setup |
| `acr_login_server` | ACR URL | Docker push/pull |
| `acr_name` | ACR name | Image references |
| `keyvault_uri` | Key Vault URI | Secret references |
| `keyvault_name` | Key Vault name | CLI operations |
| `postgresql_fqdn` | PostgreSQL FQDN (sensitive) | Connection strings |
| `resource_group_name` | Resource group name | Azure CLI commands |
| `resource_group_location` | Resource group location | New resource creation |

**Examples:**

```bash
# Get ACR login server and login
ACR_SERVER=$(terraform output -raw acr_login_server)
az acr login --name $(terraform output -raw acr_name)

# Get AKS credentials
AKS_NAME=$(terraform output -raw aks_cluster_name)
RG_NAME=$(terraform output -raw resource_group_name)
az aks get-credentials --resource-group $RG_NAME --name $AKS_NAME

# Get PostgreSQL FQDN for connection string
terraform output postgresql_fqdn
```

---

## 🔄 CI/CD Integration

Terraform can be integrated into GitHub Actions for infrastructure automation:

### Example Workflow

Create `.github/workflows/terraform.yml`:

```yaml
name: Terraform

on:
  pull_request:
    paths:
      - 'terraform/**'
  push:
    branches: [main]
    paths:
      - 'terraform/**'

jobs:
  terraform:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: terraform/environments/production

    steps:
    - uses: actions/checkout@v3

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.5.0

    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Terraform Init
      env:
        ARM_ACCESS_KEY: ${{ secrets.ARM_ACCESS_KEY }}
      run: terraform init

    - name: Terraform Format Check
      run: terraform fmt -check -recursive

    - name: Terraform Validate
      run: terraform validate

    - name: Terraform Plan
      env:
        ARM_ACCESS_KEY: ${{ secrets.ARM_ACCESS_KEY }}
      run: terraform plan -no-color

    - name: Terraform Apply
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      env:
        ARM_ACCESS_KEY: ${{ secrets.ARM_ACCESS_KEY }}
      run: terraform apply -auto-approve
```

### Required GitHub Secrets

- `ARM_ACCESS_KEY`: Storage account key for Terraform state
- `AZURE_CREDENTIALS`: Service principal credentials (JSON)

---

## 🆘 Troubleshooting

### State Lock Issues

```bash
# View active locks
az storage blob list \
  --account-name <storage-account> \
  --container-name tfstate \
  --query "[?properties.lease.state=='leased']"

# Force unlock (last resort!)
terraform force-unlock <lock-id>
```

### Import Failures

```bash
# If import fails, check resource exists
az resource show --ids <resource-id>

# Remove from state and retry
terraform state rm <resource-address>
terraform import <resource-address> <resource-id>
```

### Configuration Drift

```bash
# Detect drift from actual infrastructure
terraform plan -refresh-only

# See what changed
terraform show

# Options:
# 1. Update Terraform config to match Azure
# 2. Apply Terraform's desired state (terraform apply)
```

### Provider Version Issues

```bash
# If you get provider version conflicts
rm -rf .terraform
rm .terraform.lock.hcl
terraform init -upgrade
```

### State Corruption

```bash
# Pull current state
terraform state pull > state-backup.json

# If state is corrupted, restore from backup
az storage blob download \
  --account-name <storage-account> \
  --container-name tfstate \
  --name production.tfstate \
  --version-id <previous-version-id> \
  --file terraform.tfstate
```

---

## 📚 Module Documentation

### AKS Module

**Location:** `modules/aks/`

**Resources Created:**
- `azurerm_kubernetes_cluster.this` - AKS cluster
- `azurerm_role_assignment.acr_pull` - ACR pull permission for AKS

**Key Variables:**
- `cluster_name` - AKS cluster name
- `kubernetes_version` - K8s version (default: "1.28")
- `vm_size` - Node VM size (default: "Standard_D2s_v3")
- `node_count` - Initial nodes (default: 2)
- `enable_auto_scaling` - Enable autoscaling (default: true)
- `min_count` / `max_count` - Autoscaling limits (1-5)

**Lifecycle Rules:**
- Ignores `node_count` changes (allows autoscaling)
- Ignores `kubernetes_version` changes (prevents downgrades)

### ACR Module

**Location:** `modules/acr/`

**Resources Created:**
- `azurerm_container_registry.this` - Container registry

**Key Variables:**
- `registry_name` - ACR name
- `sku` - Pricing tier (default: "Standard")
- `admin_enabled` - Enable admin user (default: false)

### Key Vault Module

**Location:** `modules/keyvault/`

**Resources Created:**
- `azurerm_key_vault.this` - Key Vault
- `azurerm_key_vault_access_policy.terraform` - Terraform access

**Key Variables:**
- `keyvault_name` - Key Vault name
- `sku_name` - Pricing tier (default: "standard")
- `purge_protection_enabled` - Enable purge protection (default: true)
- `soft_delete_retention_days` - Soft delete retention (default: 90)

### PostgreSQL Module

**Location:** `modules/postgresql/`

**Resources Created:**
- `azurerm_postgresql_flexible_server.this` - PostgreSQL server
- `azurerm_postgresql_flexible_server_database.this` - Database
- `azurerm_postgresql_flexible_server_firewall_rule.azure_services` - Allow Azure services

**Key Variables:**
- `server_name` - PostgreSQL server name
- `postgresql_version` - PostgreSQL version (default: "14")
- `sku_name` - Pricing tier (default: "B_Standard_B1ms")
- `storage_mb` - Storage size (default: 32768)
- `backup_retention_days` - Backup retention (default: 7)

**Lifecycle Rules:**
- Ignores `administrator_password` changes

---

## 🔗 Additional Resources

- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/)
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/en-us/azure/aks/)

---

## 📞 Support

For questions or issues:

1. Check this README
2. Review `terraform plan` output for proposed changes
3. Check Azure Portal to verify actual resource state
4. Review module documentation in respective directories
5. Contact DevOps team

---

## 🔄 Maintenance

### Regular Tasks

**Weekly:**
- Review Terraform plan for any drift: `terraform plan`
- Check for provider updates: `terraform init -upgrade`

**Monthly:**
- Review and rotate secrets in Key Vault
- Check for Terraform version updates
- Review state file versions and cleanup old ones

**As Needed:**
- Update Kubernetes version in AKS module
- Adjust autoscaling limits based on usage
- Update resource SKUs for cost optimization

---

**Last Updated:** 2025-11-21
**Maintained By:** DevOps Team
**Review Schedule:** Monthly or after infrastructure changes
**Terraform Version:** >= 1.5.0
**Azure Provider Version:** ~> 3.80.0
