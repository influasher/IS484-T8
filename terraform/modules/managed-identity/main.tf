resource "azurerm_user_assigned_identity" "this" {
  name                = var.identity_name
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = var.tags
}

# Optional: Role assignments for the identity
resource "azurerm_role_assignment" "keyvault_secrets_user" {
  count                = var.keyvault_id != null ? 1 : 0
  scope                = var.keyvault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}

# Federated credential for workload identity (ESO)
resource "azurerm_federated_identity_credential" "eso" {
  count               = var.enable_workload_identity ? 1 : 0
  name                = "${var.identity_name}-eso-federated-credential"
  resource_group_name = var.resource_group_name
  parent_id           = azurerm_user_assigned_identity.this.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = var.aks_oidc_issuer_url
  subject             = "system:serviceaccount:${var.kubernetes_namespace}:${var.kubernetes_service_account}"
}
