# Azure Key Vault Secrets Setup Guide

This guide shows how to populate Azure Key Vault with the secrets needed for the SentiFinance application.

## Prerequisites

- Terraform has created the Key Vault (`sentifinance-key-vault`)
- You have Owner or Key Vault Administrator access
- Azure CLI is installed and logged in
- PostgreSQL database is created (see [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md))

---

## Required Secrets

The SentiFinance application requires these secrets in Key Vault:

| Secret Name | Description | Example Format |
|-------------|-------------|----------------|
| `DATABASE_URI` | PostgreSQL connection string | `postgresql+psycopg2://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | JWT token signing key | Random 32+ character string |
| `SECRET_KEY` | Application secret key | Random 32+ character string |

---

## Setup Methods

### Method 1: Automated Setup Script (Recommended)

Create and run a setup script to populate all secrets:

**File: `scripts/setup-secrets.sh`**

```bash
#!/bin/bash
set -e

# Configuration
KV_NAME="sentifinance-key-vault"
NAMESPACE="sentifinance"

echo "=== SentiFinance Secrets Setup ==="
echo "Key Vault: $KV_NAME"
echo ""

# Check Azure login
if ! az account show &>/dev/null; then
    echo "❌ Not logged into Azure. Run: az login"
    exit 1
fi

# Verify Key Vault exists
if ! az keyvault show --name $KV_NAME &>/dev/null; then
    echo "❌ Key Vault '$KV_NAME' not found"
    exit 1
fi

echo "✅ Key Vault found"
echo ""

# Function to generate secure random string
generate_secret() {
    openssl rand -base64 48 | tr -d "=+/" | cut -c1-64
}

# Function to set or update secret
set_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3

    echo "Setting secret: $secret_name"
    az keyvault secret set \
        --vault-name $KV_NAME \
        --name $secret_name \
        --value "$secret_value" \
        --description "$description" \
        --output none

    echo "  ✅ $secret_name set"
}

# 1. DATABASE_URI
echo "📝 DATABASE_URI Setup"
echo "  Enter PostgreSQL connection details:"
read -p "  Hostname (e.g., psql-sentifinance.postgres.database.azure.com): " DB_HOST
read -p "  Username (e.g., sentiadmin): " DB_USER
read -sp "  Password: " DB_PASS
echo ""
read -p "  Database name (default: postgres): " DB_NAME
DB_NAME=${DB_NAME:-postgres}

DATABASE_URI="postgresql+psycopg2://${DB_USER}:${DB_PASS}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

set_secret "DATABASE-URI" "$DATABASE_URI" "PostgreSQL connection string for SentiFinance app"
echo ""

# 2. JWT_SECRET_KEY
echo "📝 JWT_SECRET_KEY Setup"
JWT_SECRET=$(generate_secret)
set_secret "JWT-SECRET-KEY" "$JWT_SECRET" "JWT token signing key for authentication"
echo ""

# 3. SECRET_KEY
echo "📝 SECRET_KEY Setup"
APP_SECRET=$(generate_secret)
set_secret "SECRET-KEY" "$APP_SECRET" "Application secret key for Flask"
echo ""

# Summary
echo "=== Setup Complete ==="
echo ""
echo "✅ All secrets configured in Key Vault: $KV_NAME"
echo ""
echo "Secrets created:"
echo "  - DATABASE-URI"
echo "  - JWT-SECRET-KEY"
echo "  - SECRET-KEY"
echo ""
echo "Next steps:"
echo "  1. Deploy Kubernetes manifests (see K8S_MANIFESTS_GUIDE.md)"
echo "  2. Verify External Secrets Operator syncs secrets"
echo "  3. Restart application pods if needed"
echo ""
```

**Run the script:**

```bash
chmod +x scripts/setup-secrets.sh
./scripts/setup-secrets.sh
```

---

### Method 2: Manual Setup via Azure CLI

Set secrets one by one:

#### 1. DATABASE_URI

```bash
# Build connection string from PostgreSQL details
DB_USER="sentiadmin"
DB_PASS="YourSecurePassword123!"
DB_HOST="psql-sentifinance-prod.postgres.database.azure.com"
DB_NAME="postgres"

DATABASE_URI="postgresql+psycopg2://${DB_USER}:${DB_PASS}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

# Set in Key Vault
az keyvault secret set \
  --vault-name sentifinance-key-vault \
  --name DATABASE-URI \
  --value "$DATABASE_URI" \
  --description "PostgreSQL connection string"

# Verify
az keyvault secret show \
  --vault-name sentifinance-key-vault \
  --name DATABASE-URI \
  --query "value" -o tsv
```

#### 2. JWT_SECRET_KEY

```bash
# Generate secure random key
JWT_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)

# Set in Key Vault
az keyvault secret set \
  --vault-name sentifinance-key-vault \
  --name JWT-SECRET-KEY \
  --value "$JWT_SECRET" \
  --description "JWT token signing key"

echo "JWT Secret generated and stored"
```

#### 3. SECRET_KEY

```bash
# Generate secure random key
APP_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)

# Set in Key Vault
az keyvault secret set \
  --vault-name sentifinance-key-vault \
  --name SECRET-KEY \
  --value "$APP_SECRET" \
  --description "Flask application secret key"

echo "App secret generated and stored"
```

---

### Method 3: Azure Portal (Manual)

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Key Vaults** → **sentifinance-key-vault**
3. Click **Secrets** in left menu
4. Click **+ Generate/Import**
5. Fill in:
   - **Upload options:** Manual
   - **Name:** DATABASE-URI (use hyphens, not underscores)
   - **Value:** `postgresql+psycopg2://...`
   - **Content type:** (optional) `connection-string`
6. Click **Create**
7. Repeat for JWT-SECRET-KEY and SECRET-KEY

---

## Secret Naming Convention

**Important:** External Secrets Operator converts hyphens to underscores:

| Key Vault Secret Name | Kubernetes Secret Key | Environment Variable |
|-----------------------|-----------------------|----------------------|
| `DATABASE-URI` | `DATABASE_URI` | `DATABASE_URI` |
| `JWT-SECRET-KEY` | `JWT_SECRET_KEY` | `JWT_SECRET_KEY` |
| `SECRET-KEY` | `SECRET_KEY` | `SECRET_KEY` |

**Use hyphens in Key Vault**, they become underscores in Kubernetes.

---

## Verify Secrets Are Set

```bash
# List all secrets
az keyvault secret list \
  --vault-name sentifinance-key-vault \
  --query "[].name" -o tsv

# Expected output:
# DATABASE-URI
# JWT-SECRET-KEY
# SECRET-KEY

# Show secret metadata (not value)
az keyvault secret show \
  --vault-name sentifinance-key-vault \
  --name DATABASE-URI \
  --query "{name:name, contentType:contentType, created:attributes.created}"

# Get secret value (for verification only - DO NOT LOG)
az keyvault secret show \
  --vault-name sentifinance-key-vault \
  --name DATABASE-URI \
  --query "value" -o tsv
```

---

## External Secrets Operator Configuration

After setting secrets in Key Vault, External Secrets Operator (ESO) syncs them to Kubernetes.

### Verify ESO is Installed

```bash
# Check ESO is running
kubectl get pods -n external-secrets-operator

# Should show external-secrets pods running
```

### Check SecretStore Configuration

```bash
# View SecretStore (connects K8s to Key Vault)
kubectl get secretstore -n sentifinance

# View details
kubectl describe secretstore azure-secret-store -n sentifinance
```

**Expected SecretStore configuration:**

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

### Check ExternalSecret Configuration

```bash
# View ExternalSecret (defines which secrets to sync)
kubectl get externalsecret -n sentifinance

# View details
kubectl describe externalsecret sentifinance-secrets -n sentifinance
```

**Expected ExternalSecret configuration:**

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

### Verify Kubernetes Secret is Created

```bash
# Check if secret was created by ESO
kubectl get secret sentifinance-app-secrets -n sentifinance

# View secret keys (not values)
kubectl describe secret sentifinance-app-secrets -n sentifinance

# Get secret value (for debugging only)
kubectl get secret sentifinance-app-secrets -n sentifinance \
  -o jsonpath='{.data.DATABASE_URI}' | base64 -d
```

---

## Troubleshooting

### Secret Not Syncing to Kubernetes

```bash
# 1. Check ExternalSecret status
kubectl describe externalsecret sentifinance-secrets -n sentifinance

# Look for errors in Events section

# 2. Check ESO logs
kubectl logs -n external-secrets-operator \
  -l app.kubernetes.io/name=external-secrets --tail=100

# 3. Check workload identity
kubectl describe sa external-secrets-sa -n sentifinance

# Should show annotation:
# azure.workload.identity/client-id: <client-id>

# 4. Verify managed identity has Key Vault access
az role assignment list \
  --assignee <managed-identity-client-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/sentifinance.azurecr.io/providers/Microsoft.KeyVault/vaults/sentifinance-key-vault
```

### Permission Denied Errors

```bash
# Grant "Key Vault Secrets User" role to ESO managed identity
IDENTITY_PRINCIPAL_ID=$(az identity show \
  --name sentifinance-secrets-identity \
  --resource-group sentifinance.azurecr.io \
  --query principalId -o tsv)

KV_ID=$(az keyvault show \
  --name sentifinance-key-vault \
  --query id -o tsv)

az role assignment create \
  --assignee $IDENTITY_PRINCIPAL_ID \
  --role "Key Vault Secrets User" \
  --scope $KV_ID
```

### Secret Values Incorrect

```bash
# Update secret in Key Vault
az keyvault secret set \
  --vault-name sentifinance-key-vault \
  --name DATABASE-URI \
  --value "NEW-VALUE"

# Force ESO to refresh (delete and recreate K8s secret)
kubectl delete externalsecret sentifinance-secrets -n sentifinance
kubectl apply -f k8s/external-secret.yaml

# Or restart ESO pods to force sync
kubectl rollout restart deployment external-secrets -n external-secrets-operator
```

---

## Rotating Secrets

### Rotate JWT/App Secrets

```bash
# 1. Generate new secret
NEW_JWT_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)

# 2. Update in Key Vault
az keyvault secret set \
  --vault-name sentifinance-key-vault \
  --name JWT-SECRET-KEY \
  --value "$NEW_JWT_SECRET"

# 3. Wait for ESO to sync (default: 1 hour) or force:
kubectl delete pod -n sentifinance -l app=sentifinance-backend

# 4. Pods will restart with new secret
```

### Rotate Database Password

```bash
# 1. Update PostgreSQL password
az postgres flexible-server update \
  --resource-group sentifinance-db-rg \
  --name psql-sentifinance-prod \
  --admin-password "NewSecurePassword123!"

# 2. Update connection string in Key Vault
DATABASE_URI="postgresql+psycopg2://sentiadmin:NewSecurePassword123@psql-sentifinance-prod.postgres.database.azure.com:5432/postgres?sslmode=require"

az keyvault secret set \
  --vault-name sentifinance-key-vault \
  --name DATABASE-URI \
  --value "$DATABASE_URI"

# 3. Restart application
kubectl rollout restart deployment sentifinance-backend -n sentifinance
```

---

## Security Best Practices

### 1. Never Log or Print Secrets

```bash
# ❌ BAD - Don't do this
echo "DATABASE_URI=$DATABASE_URI"
az keyvault secret show --name DATABASE-URI --vault-name kv --query value

# ✅ GOOD - Verify without showing value
az keyvault secret show --name DATABASE-URI --vault-name kv --query name
```

### 2. Use Service Principal or Managed Identity

```bash
# For CI/CD, create service principal with minimal permissions
az ad sp create-for-rbac --name "github-actions-sp" \
  --role "Key Vault Secrets User" \
  --scopes /subscriptions/.../resourceGroups/.../providers/Microsoft.KeyVault/vaults/sentifinance-key-vault
```

### 3. Enable Key Vault Auditing

```bash
# Enable diagnostic logs
az monitor diagnostic-settings create \
  --resource $(az keyvault show --name sentifinance-key-vault --query id -o tsv) \
  --name kv-audit-logs \
  --workspace <log-analytics-workspace-id> \
  --logs '[{"category": "AuditEvent", "enabled": true}]'
```

### 4. Use RBAC Instead of Access Policies

```bash
# Check if RBAC is enabled
az keyvault show --name sentifinance-key-vault \
  --query properties.enableRbacAuthorization

# If false, enable RBAC (requires recreation or update)
az keyvault update --name sentifinance-key-vault \
  --enable-rbac-authorization true
```

---

## Backup and Restore

### Backup Secrets

```bash
# Export secret names and metadata (not values)
az keyvault secret list \
  --vault-name sentifinance-key-vault \
  --query "[].{name:name, contentType:contentType}" \
  -o json > secrets-backup-metadata.json

# For disaster recovery, document:
# 1. How to regenerate JWT/SECRET keys (random)
# 2. How to get DATABASE_URI (from PostgreSQL admin)
# 3. Store backup in secure location (1Password, etc.)
```

### Restore After Disaster

```bash
# Key Vault has soft-delete enabled, so deleted secrets can be recovered
az keyvault secret recover \
  --vault-name sentifinance-key-vault \
  --name DATABASE-URI

# If Key Vault was deleted, recreate and re-run setup script
./scripts/setup-secrets.sh
```

---

## Next Steps

1. ✅ Secrets created in Key Vault
2. ✅ ESO configured to sync secrets
3. 📝 Configure Kubernetes manifests → See [K8S_MANIFESTS_GUIDE.md](K8S_MANIFESTS_GUIDE.md)
4. 📝 Deploy application
5. 📝 Verify pods can access secrets

---

**Created:** 2025-11-22
**Last Updated:** 2025-11-22
**Maintained By:** DevOps Team
