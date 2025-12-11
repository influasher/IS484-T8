output "identity_id" {
  description = "Managed identity ID"
  value       = azurerm_user_assigned_identity.this.id
}

output "identity_name" {
  description = "Managed identity name"
  value       = azurerm_user_assigned_identity.this.name
}

output "client_id" {
  description = "Client ID (Application ID)"
  value       = azurerm_user_assigned_identity.this.client_id
}

output "principal_id" {
  description = "Principal ID (Object ID)"
  value       = azurerm_user_assigned_identity.this.principal_id
}

output "tenant_id" {
  description = "Tenant ID"
  value       = azurerm_user_assigned_identity.this.tenant_id
}
