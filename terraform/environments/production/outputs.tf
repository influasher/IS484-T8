# AKS Outputs
output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = module.aks.cluster_name
}

output "aks_cluster_id" {
  description = "AKS cluster ID"
  value       = module.aks.cluster_id
}

output "aks_oidc_issuer_url" {
  description = "AKS OIDC issuer URL"
  value       = module.aks.oidc_issuer_url
}

# ACR Outputs
output "acr_login_server" {
  description = "ACR login server URL"
  value       = module.acr.login_server
}

output "acr_name" {
  description = "ACR name"
  value       = module.acr.registry_name
}

# Key Vault Outputs
output "keyvault_uri" {
  description = "Key Vault URI"
  value       = module.keyvault.keyvault_uri
}

output "keyvault_name" {
  description = "Key Vault name"
  value       = module.keyvault.keyvault_name
}

# PostgreSQL Outputs
# NOTE: PostgreSQL module is commented out (separate subscription)
# output "postgresql_fqdn" {
#   description = "PostgreSQL server FQDN"
#   value       = module.postgresql.server_fqdn
#   sensitive   = true
# }

# Storage Account Outputs
output "storage_account_name" {
  description = "Storage account name"
  value       = module.storage.storage_account_name
}

output "storage_primary_blob_endpoint" {
  description = "Storage account primary blob endpoint"
  value       = module.storage.primary_blob_endpoint
}

# Virtual Network Outputs
output "vnet_id" {
  description = "Virtual network ID"
  value       = module.vnet.vnet_id
}

output "vnet_name" {
  description = "Virtual network name"
  value       = module.vnet.vnet_name
}

output "subnet_ids" {
  description = "Map of subnet names to IDs"
  value       = module.vnet.subnet_ids
}

# Managed Identity Outputs
output "eso_identity_client_id" {
  description = "ESO identity client ID"
  value       = module.eso_identity.client_id
}

output "eso_identity_principal_id" {
  description = "ESO identity principal ID"
  value       = module.eso_identity.principal_id
}

output "additional_identity_client_id" {
  description = "Additional identity client ID"
  value       = module.additional_identity.client_id
}

# Application Gateway Outputs
output "app_gateway_id" {
  description = "Application Gateway for Containers ID"
  value       = module.app_gateway.traffic_controller_id
}

output "app_gateway_name" {
  description = "Application Gateway for Containers name"
  value       = module.app_gateway.traffic_controller_name
}

# Resource Group Outputs
output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Resource group location"
  value       = azurerm_resource_group.main.location
}

output "resource_group_id" {
  description = "Resource group ID"
  value       = azurerm_resource_group.main.id
}
