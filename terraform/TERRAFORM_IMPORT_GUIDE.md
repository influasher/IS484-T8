# Terraform Import Guide

This guide provides step-by-step instructions for importing your existing Azure infrastructure into Terraform state.

## Prerequisites

1. Azure CLI logged in with correct subscription
2. Terraform >= 1.5.0 installed
3. ARM_ACCESS_KEY environment variable set (for remote state access)
4. Current working directory: `terraform/environments/production`

```bash
# Verify prerequisites
az account show
terraform version
echo $ARM_ACCESS_KEY

# Navigate to production environment
cd terraform/environments/production
```

## Step 1: Initialize Terraform

```bash
# Initialize Terraform (downloads providers and configures backend)
terraform init

# Expected output: Successfully configured backend and initialized providers
```

## Step 2: Get Azure Resource IDs

Run these commands to get the resource IDs needed for import:

```bash
# Set variables
export RG_NAME="sentifinance.azurecr.io"
export LOCATION="southeastasia"

# Get Resource Group ID
export RG_ID=$(az group show --name $RG_NAME --query id -o tsv)
echo "Resource Group ID: $RG_ID"

# Get ACR ID
export ACR_ID=$(az acr show --name sentifinancetwo --resource-group $RG_NAME --query id -o tsv)
echo "ACR ID: $ACR_ID"

# Get AKS ID
export AKS_ID=$(az aks show --name sentifinance-k8 --resource-group $RG_NAME --query id -o tsv)
echo "AKS ID: $AKS_ID"

# Get Key Vault ID
export KV_ID=$(az keyvault show --name sentifinance-key-vault --query id -o tsv)
echo "Key Vault ID: $KV_ID"

# Get Storage Account ID
export STORAGE_ID=$(az storage account show --name sentifinanceblob --resource-group $RG_NAME --query id -o tsv)
echo "Storage ID: $STORAGE_ID"

# Get VNet ID
export VNET_ID=$(az network vnet show --name sentifinance.azurecr.io-vnet --resource-group $RG_NAME --query id -o tsv)
echo "VNet ID: $VNET_ID"

# Get Subnet IDs
export SUBNET_DEFAULT_ID=$(az network vnet subnet show --vnet-name sentifinance.azurecr.io-vnet --name default --resource-group $RG_NAME --query id -o tsv)
export SUBNET_ACI_ID=$(az network vnet subnet show --vnet-name sentifinance.azurecr.io-vnet --name virtual-node-aci --resource-group $RG_NAME --query id -o tsv)
export SUBNET_APPGW_ID=$(az network vnet subnet show --vnet-name sentifinance.azurecr.io-vnet --name ingress-appgateway-subnet --resource-group $RG_NAME --query id -o tsv)

# Get Managed Identity IDs
export ESO_ID=$(az identity show --name sentifinance-secrets-identity --resource-group $RG_NAME --query id -o tsv)
export ADDITIONAL_ID=$(az identity show --name ua-id-ba65 --resource-group $RG_NAME --query id -o tsv)

# Get Application Gateway for Containers ID
export APPGW_ID=$(az resource show --resource-group $RG_NAME --name sentifinance-app-gateway --resource-type "Microsoft.ServiceNetworking/trafficControllers" --query id -o tsv)

# Print all IDs for verification
echo "=== All Resource IDs ==="
echo "RG: $RG_ID"
echo "ACR: $ACR_ID"
echo "AKS: $AKS_ID"
echo "KV: $KV_ID"
echo "STORAGE: $STORAGE_ID"
echo "VNET: $VNET_ID"
echo "SUBNET_DEFAULT: $SUBNET_DEFAULT_ID"
echo "SUBNET_ACI: $SUBNET_ACI_ID"
echo "SUBNET_APPGW: $SUBNET_APPGW_ID"
echo "ESO: $ESO_ID"
echo "ADDITIONAL: $ADDITIONAL_ID"
echo "APPGW: $APPGW_ID"
```

## Step 3: Import Resources (In Dependency Order)

Import resources in the correct order to respect dependencies:

### 3.1 Resource Group

```bash
terraform import azurerm_resource_group.main "$RG_ID"

# Expected: Import successful! Resources: 1 imported, 0 added, 0 changed, 0 destroyed
```

### 3.2 Virtual Network and Subnets

```bash
# Import VNet first
terraform import module.vnet.azurerm_virtual_network.this "$VNET_ID"

# Import subnets (use exact key names from the module)
terraform import 'module.vnet.azurerm_subnet.subnets["default"]' "$SUBNET_DEFAULT_ID"
terraform import 'module.vnet.azurerm_subnet.subnets["virtual-node-aci"]' "$SUBNET_ACI_ID"
terraform import 'module.vnet.azurerm_subnet.subnets["ingress-appgateway-subnet"]' "$SUBNET_APPGW_ID"
```

### 3.3 Storage Account

```bash
terraform import module.storage.azurerm_storage_account.this "$STORAGE_ID"
```

### 3.4 Container Registry (ACR)

```bash
terraform import module.acr.azurerm_container_registry.this "$ACR_ID"
```

### 3.5 AKS Cluster

```bash
# Import AKS cluster
terraform import module.aks.azurerm_kubernetes_cluster.this "$AKS_ID"

# Import ACR role assignment (get the assignment ID)
export ACR_ROLE_ID=$(az role assignment list --scope "$ACR_ID" --query "[?roleDefinitionName=='AcrPull' && principalType=='ServicePrincipal'].id | [0]" -o tsv)
terraform import 'module.aks.azurerm_role_assignment.acr_pull[0]' "$ACR_ROLE_ID"
```

### 3.6 Key Vault

```bash
terraform import module.keyvault.azurerm_key_vault.this "$KV_ID"

# Import Terraform service principal's access policy (if exists)
# Note: Access policy ID format: {keyvault-id}/objectId/{object-id}
export CURRENT_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
terraform import 'module.keyvault.azurerm_key_vault_access_policy.terraform' "${KV_ID}/objectId/${CURRENT_OBJECT_ID}"
```

### 3.7 Managed Identities

```bash
# Import ESO identity
terraform import module.eso_identity.azurerm_user_assigned_identity.this "$ESO_ID"

# Import ESO KeyVault role assignment
export ESO_KV_ROLE_ID=$(az role assignment list --scope "$KV_ID" --assignee $(az identity show --ids "$ESO_ID" --query principalId -o tsv) --query "[?roleDefinitionName=='Key Vault Secrets User'].id | [0]" -o tsv)
terraform import 'module.eso_identity.azurerm_role_assignment.keyvault_secrets_user[0]' "$ESO_KV_ROLE_ID"

# Import ESO federated credential (if exists)
export FED_CRED_ID="${ESO_ID}/federatedIdentityCredentials/sentifinance-secrets-identity-eso-federated-credential"
terraform import 'module.eso_identity.azurerm_federated_identity_credential.eso[0]' "$FED_CRED_ID"

# Import additional identity
terraform import module.additional_identity.azurerm_user_assigned_identity.this "$ADDITIONAL_ID"
```

### 3.8 Application Gateway for Containers

```bash
# Import traffic controller
terraform import module.app_gateway.azapi_resource.traffic_controller "$APPGW_ID"

# Import association (if exists)
# Note: This may fail if association doesn't exist yet - that's okay
export ASSOC_ID="${APPGW_ID}/associations/sentifinance-app-gateway-association"
terraform import 'module.app_gateway.azapi_resource.association[0]' "$ASSOC_ID" || echo "Association not found - will be created"
```

## Step 4: Verify Imports

```bash
# List all imported resources
terraform state list

# Expected output should show all these resources:
# - azurerm_resource_group.main
# - module.vnet.azurerm_virtual_network.this
# - module.vnet.azurerm_subnet.subnets["default"]
# - module.vnet.azurerm_subnet.subnets["virtual-node-aci"]
# - module.vnet.azurerm_subnet.subnets["ingress-appgateway-subnet"]
# - module.storage.azurerm_storage_account.this
# - module.acr.azurerm_container_registry.this
# - module.aks.azurerm_kubernetes_cluster.this
# - module.aks.azurerm_role_assignment.acr_pull[0]
# - module.keyvault.azurerm_key_vault.this
# - module.keyvault.azurerm_key_vault_access_policy.terraform
# - module.eso_identity.azurerm_user_assigned_identity.this
# - module.eso_identity.azurerm_role_assignment.keyvault_secrets_user[0]
# - module.eso_identity.azurerm_federated_identity_credential.eso[0]
# - module.additional_identity.azurerm_user_assigned_identity.this
# - module.app_gateway.azapi_resource.traffic_controller

# Count resources
terraform state list | wc -l

# Expected: ~17 resources (may vary based on what exists)
```

## Step 5: Align Configuration with Reality

After importing, you need to ensure Terraform's configuration matches Azure's actual state:

```bash
# Run terraform plan to see differences
terraform plan

# Common differences you might see:
# 1. Tags might be different
# 2. Some computed values might differ
# 3. Optional attributes not set in Terraform

# To fix differences:
# - Update terraform.tfvars with actual values
# - Adjust module parameters in main.tf
# - Use lifecycle blocks to ignore_changes for computed values
```

## Step 6: Create terraform.tfvars

```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit with actual values (already filled in example)
# No changes needed - example file has correct values

# Verify configuration
terraform validate

# Expected: Success! The configuration is valid.
```

## Step 7: Final Verification

```bash
# Run plan again - should show minimal or no changes
terraform plan

# Ideal output: "No changes. Your infrastructure matches the configuration."

# If there are still differences, review and fix:
# - Check actual resource configurations in Azure Portal
# - Update Terraform variables to match
# - Use lifecycle ignore_changes for attributes you don't want to manage
```

## Troubleshooting

### Import Fails: Resource Not Found

```bash
# Verify resource exists
az resource show --ids <resource-id>

# If resource doesn't exist, remove from Terraform config
# If resource exists but ID is wrong, get correct ID
```

### Import Fails: Already Exists in State

```bash
# Remove from state first
terraform state rm <resource-address>

# Then re-import
terraform import <resource-address> <resource-id>
```

### Plan Shows Unwanted Changes

```bash
# Option 1: Update Terraform config to match Azure
# Edit the module variables or main.tf

# Option 2: Use lifecycle ignore_changes
# Add to resource block:
lifecycle {
  ignore_changes = [
    attribute_name,
  ]
}

# Option 3: If change is acceptable, apply it
terraform apply
```

### Federated Credential Import Fails

```bash
# Check if federated credential exists
az identity federated-credential list --identity-name sentifinance-secrets-identity --resource-group $RG_NAME

# If it doesn't exist, remove from import list - Terraform will create it
# If it exists, verify the exact name and retry
```

### Access Policy Import Fails

```bash
# List access policies
az keyvault show --name sentifinance-key-vault --query properties.accessPolicies

# If your object ID doesn't have a policy, skip this import
# The module will create it on first apply
```

## Post-Import Checklist

- [ ] All resources imported successfully
- [ ] `terraform state list` shows all expected resources
- [ ] `terraform plan` shows no changes (or only acceptable changes)
- [ ] `terraform validate` passes
- [ ] terraform.tfvars created with actual values
- [ ] Remote state is accessible and up-to-date
- [ ] Team members can access remote state

## Next Steps

After successful import:

1. **Test Terraform Operations**
   ```bash
   # Test plan (should show no changes)
   terraform plan

   # Test apply (if there are minor acceptable changes)
   terraform apply
   ```

2. **Document Exceptions**
   - PostgreSQL is in separate subscription (not managed)
   - Monitoring resources are auto-created by AKS (not managed)
   - Any other resources intentionally not managed by Terraform

3. **Set Up CI/CD for Terraform** (Optional)
   - Add GitHub Actions workflow for terraform plan on PRs
   - Add terraform apply on merges to main
   - See: `.github/workflows/terraform.yml` (example in README)

4. **Regular Maintenance**
   - Run `terraform plan` weekly to detect drift
   - Update Kubernetes version in AKS module when needed
   - Review and update provider versions quarterly

## Resources

- [Terraform Import Documentation](https://developer.hashicorp.com/terraform/cli/import)
- [Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Project Terraform README](README.md)

---

**Last Updated:** 2025-11-22
**Import Tested:** Yes
**Estimated Time:** 30-45 minutes
