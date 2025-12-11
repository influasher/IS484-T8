# PostgreSQL Database Setup Guide

This guide shows how to create a PostgreSQL Flexible Server using Terraform for the SentiFinance application.

## Option 1: Same Subscription (Recommended for New Deployment)

If you want to manage PostgreSQL in the same Terraform configuration:

### Step 1: Uncomment PostgreSQL Module

Edit `terraform/environments/production/main.tf` and uncomment the PostgreSQL module:

```hcl
# PostgreSQL Module
module "postgresql" {
  source = "../../modules/postgresql"

  server_name         = var.postgresql_server_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  # Update these credentials (will be stored in Terraform state - use carefully)
  admin_username      = "sentiadmin"
  admin_password      = var.postgresql_admin_password  # Add this variable

  # Database configuration
  database_name       = "postgres"
  postgresql_version  = "14"
  sku_name            = "B_Standard_B1ms"  # Basic tier for dev/test
  storage_mb          = 32768  # 32 GB

  # Backup configuration
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false  # Set true for production

  tags = var.tags
}
```

### Step 2: Add PostgreSQL Password Variable

Edit `terraform/environments/production/variables.tf` and add:

```hcl
variable "postgresql_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}
```

### Step 3: Set Password in terraform.tfvars

Edit `terraform/environments/production/terraform.tfvars` (gitignored):

```hcl
# Add to terraform.tfvars (NOT tfvars.example - it's gitignored)
postgresql_admin_password = "YourSecurePassword123!"  # Change this!

# Or better: use environment variable
# export TF_VAR_postgresql_admin_password="YourSecurePassword123!"
```

### Step 4: Uncomment PostgreSQL Output

Edit `terraform/environments/production/outputs.tf`:

```hcl
# PostgreSQL Outputs
output "postgresql_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = module.postgresql.server_fqdn
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = module.postgresql.database_name
}
```

### Step 5: Apply Terraform

```bash
cd terraform/environments/production

# Initialize (if not already done)
terraform init

# Plan to see what will be created
terraform plan

# Apply to create PostgreSQL
terraform apply

# Get the connection details
terraform output postgresql_fqdn
terraform output database_name
```

### Step 6: Get Connection String

```bash
# Build connection string
FQDN=$(terraform output -raw postgresql_fqdn)
DB_NAME=$(terraform output -raw database_name)
USERNAME="sentiadmin"
PASSWORD="YourSecurePassword123!"  # The password you set

CONNECTION_STRING="postgresql+psycopg2://${USERNAME}:${PASSWORD}@${FQDN}:5432/${DB_NAME}"

echo "Connection String: $CONNECTION_STRING"

# Store this in Azure Key Vault (see SECRETS_SETUP.md)
```

---

## Option 2: Separate Subscription (Current Setup)

If PostgreSQL is in a different Azure subscription:

### Step 1: Create Separate Terraform Configuration

Create `terraform/environments/database/` directory:

```bash
mkdir -p terraform/environments/database
```

### Step 2: Create Database-Specific Configuration

**File: `terraform/environments/database/main.tf`**

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80.0"
    }
  }
}

provider "azurerm" {
  features {}

  # Use different subscription
  subscription_id = var.database_subscription_id
}

# Use existing resource group or create new one
data "azurerm_resource_group" "db" {
  name = var.database_resource_group_name
}

# PostgreSQL Flexible Server
module "postgresql" {
  source = "../../modules/postgresql"

  server_name         = "psql-sentifinance-prod"
  resource_group_name = data.azurerm_resource_group.db.name
  location            = data.azurerm_resource_group.db.location

  admin_username      = "sentiadmin"
  admin_password      = var.postgresql_admin_password

  database_name       = "postgres"
  postgresql_version  = "14"
  sku_name            = "B_Standard_B1ms"
  storage_mb          = 32768

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  tags = {
    Environment = "production"
    Project     = "SentiFinance"
    ManagedBy   = "Terraform"
  }
}
```

**File: `terraform/environments/database/variables.tf`**

```hcl
variable "database_subscription_id" {
  description = "Azure subscription ID for database"
  type        = string
}

variable "database_resource_group_name" {
  description = "Resource group for database"
  type        = string
  default     = "sentifinance-database-rg"
}

variable "postgresql_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}
```

**File: `terraform/environments/database/terraform.tfvars.example`**

```hcl
database_subscription_id      = "YOUR-DATABASE-SUBSCRIPTION-ID"
database_resource_group_name  = "sentifinance-database-rg"
# postgresql_admin_password is set via environment variable
```

### Step 3: Apply Database Terraform

```bash
cd terraform/environments/database

# Copy example
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your subscription ID

# Set password via environment variable (more secure)
export TF_VAR_postgresql_admin_password="YourSecurePassword123!"

# Login to Azure with database subscription
az login
az account set --subscription "YOUR-DATABASE-SUBSCRIPTION-ID"

# Initialize and apply
terraform init
terraform apply
```

---

## Database Schema Setup

After creating PostgreSQL server, you need to create the application schema.

### Step 1: Connect to Database

```bash
# Install psql client (if not installed)
# macOS
brew install libpq
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# Ubuntu/Debian
sudo apt-get install postgresql-client

# Connect to database
PGPASSWORD="YourSecurePassword123!" psql \
  -h psql-sentifinance-prod.postgres.database.azure.com \
  -U sentiadmin \
  -d postgres
```

### Step 2: Run Database Migrations

If you have migration scripts:

```bash
# Option 1: Using Alembic (Python)
cd Backend
alembic upgrade head

# Option 2: Using SQL scripts
psql -h $DB_HOST -U sentiadmin -d postgres -f schema.sql

# Option 3: Application auto-migration
# Some frameworks run migrations on startup
```

### Step 3: Verify Schema

```sql
-- Connect to database
\c postgres

-- List tables
\dt

-- Check specific tables
SELECT * FROM information_schema.tables
WHERE table_schema = 'public';
```

---

## Security Best Practices

### 1. Use Environment Variables for Passwords

**Never commit passwords to Git!**

```bash
# Set via environment variable
export TF_VAR_postgresql_admin_password="$(openssl rand -base64 32)"

# Or use Azure Key Vault to generate and store
az keyvault secret set \
  --vault-name sentifinance-key-vault \
  --name postgresql-admin-password \
  --value "$(openssl rand -base64 32)"
```

### 2. Configure Firewall Rules

**Allow specific IP ranges only:**

```hcl
# In postgresql module, add firewall rules
resource "azurerm_postgresql_flexible_server_firewall_rule" "office" {
  name             = "AllowOfficeIP"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = "203.0.113.0"  # Your office IP
  end_ip_address   = "203.0.113.255"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
```

### 3. Enable SSL/TLS

PostgreSQL Flexible Server enforces SSL by default. Ensure your application uses SSL:

```python
# Python connection string
DATABASE_URI = "postgresql+psycopg2://user:pass@host:5432/db?sslmode=require"
```

### 4. Regular Backups

```bash
# Manual backup
az postgres flexible-server backup create \
  --resource-group sentifinance-rg \
  --name psql-sentifinance-prod \
  --backup-name manual-backup-$(date +%Y%m%d)

# Automated backups are configured in Terraform:
# backup_retention_days = 7
# geo_redundant_backup_enabled = false (or true for production)
```

---

## Connection String Format

The application expects the connection string in this format:

```bash
# Format
postgresql+psycopg2://USERNAME:PASSWORD@HOSTNAME:5432/DATABASE

# Example
postgresql+psycopg2://sentiadmin:SecurePass123@psql-sentifinance-prod.postgres.database.azure.com:5432/postgres

# With SSL (recommended)
postgresql+psycopg2://sentiadmin:SecurePass123@psql-sentifinance-prod.postgres.database.azure.com:5432/postgres?sslmode=require
```

**Store this in Azure Key Vault** (see [SECRETS_SETUP.md](SECRETS_SETUP.md))

---

## Troubleshooting

### Cannot Connect to Database

```bash
# 1. Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group sentifinance-rg \
  --name psql-sentifinance-prod

# 2. Check server status
az postgres flexible-server show \
  --resource-group sentifinance-rg \
  --name psql-sentifinance-prod \
  --query state

# 3. Test connection
psql -h psql-sentifinance-prod.postgres.database.azure.com \
     -U sentiadmin \
     -d postgres \
     -c "SELECT version();"
```

### Password Authentication Failed

```bash
# Reset admin password
az postgres flexible-server update \
  --resource-group sentifinance-rg \
  --name psql-sentifinance-prod \
  --admin-password "NewSecurePassword123!"
```

### Database Migration Fails

```bash
# Check database exists
psql -h $HOST -U sentiadmin -d postgres -c "\l"

# Check user permissions
psql -h $HOST -U sentiadmin -d postgres -c "\du"

# Grant all permissions if needed
psql -h $HOST -U sentiadmin -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE postgres TO sentiadmin;"
```

---

## Cost Optimization

### Development/Testing

```hcl
sku_name            = "B_Standard_B1ms"  # ~$15/month
storage_mb          = 32768              # 32 GB
backup_retention_days = 7
geo_redundant_backup_enabled = false
```

### Production

```hcl
sku_name            = "GP_Standard_D2s_v3"  # ~$180/month
storage_mb          = 131072                # 128 GB
backup_retention_days = 30
geo_redundant_backup_enabled = true
high_availability_mode = "ZoneRedundant"
```

---

## Next Steps

1. ✅ Create PostgreSQL server via Terraform
2. ✅ Get connection string
3. 📝 Store connection string in Key Vault → See [SECRETS_SETUP.md](SECRETS_SETUP.md)
4. 📝 Run database migrations
5. 📝 Configure application to use database → See [K8S_MANIFESTS_GUIDE.md](K8S_MANIFESTS_GUIDE.md)

---

**Created:** 2025-11-22
**Last Updated:** 2025-11-22
**Maintained By:** DevOps Team
