variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "southeastasia"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "sentifinance.azurecr.io"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "sentifinance"
}

variable "aks_cluster_name" {
  description = "AKS cluster name"
  type        = string
  default     = "sentifinance-k8"
}

variable "acr_name" {
  description = "Azure Container Registry name"
  type        = string
  default     = "sentifinancetwo"
}

variable "keyvault_name" {
  description = "Key Vault name"
  type        = string
  default     = "sentifinance-key-vault"
}

variable "postgresql_server_name" {
  description = "PostgreSQL server name (in separate subscription)"
  type        = string
  default     = "psql-sentifinance-dev"
}

variable "storage_account_name" {
  description = "Storage account name"
  type        = string
  default     = "sentifinanceblob"
}

variable "storage_location" {
  description = "Storage account location"
  type        = string
  default     = "eastus"
}

variable "vnet_name" {
  description = "Virtual network name"
  type        = string
  default     = "sentifinance.azurecr.io-vnet"
}

variable "vnet_address_space" {
  description = "Virtual network address space"
  type        = list(string)
  default     = ["10.224.0.0/12"]
}

variable "eso_identity_name" {
  description = "External Secrets Operator identity name"
  type        = string
  default     = "sentifinance-secrets-identity"
}

variable "additional_identity_name" {
  description = "Additional managed identity name"
  type        = string
  default     = "ua-id-ba65"
}

variable "app_gateway_name" {
  description = "Application Gateway for Containers name"
  type        = string
  default     = "sentifinance-app-gateway"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "SentiFinance"
    ManagedBy   = "Terraform"
  }
}
