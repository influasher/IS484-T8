variable "identity_name" {
  description = "Managed identity name"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "keyvault_id" {
  description = "Key Vault ID to grant access to (optional)"
  type        = string
  default     = null
}

variable "enable_workload_identity" {
  description = "Enable federated credential for workload identity (ESO)"
  type        = bool
  default     = false
}

variable "aks_oidc_issuer_url" {
  description = "AKS OIDC issuer URL (required if enable_workload_identity is true)"
  type        = string
  default     = ""
}

variable "kubernetes_namespace" {
  description = "Kubernetes namespace for service account (required if enable_workload_identity is true)"
  type        = string
  default     = "sentifinance"
}

variable "kubernetes_service_account" {
  description = "Kubernetes service account name (required if enable_workload_identity is true)"
  type        = string
  default     = "external-secrets-sa"
}

variable "tags" {
  description = "Tags to apply to managed identity"
  type        = map(string)
  default     = {}
}
