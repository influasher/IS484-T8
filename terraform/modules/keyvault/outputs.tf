output "keyvault_id" {
  description = "Key Vault ID"
  value       = azurerm_key_vault.this.id
}

output "keyvault_name" {
  description = "Key Vault name"
  value       = azurerm_key_vault.this.name
}

output "keyvault_uri" {
  description = "Key Vault URI"
  value       = azurerm_key_vault.this.vault_uri
}
