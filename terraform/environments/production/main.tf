terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.45.0"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.9.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy       = false
      recover_soft_deleted_key_vaults    = true
    }

    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

provider "azuread" {}

provider "azapi" {}

# Data source for current client
data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags

  lifecycle {
    prevent_destroy = true  # Safety measure
  }
}

# Virtual Network Module
module "vnet" {
  source = "../../modules/vnet"

  vnet_name           = var.vnet_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  address_space       = var.vnet_address_space

  subnets = [
    {
      name           = "default"
      address_prefix = "10.224.0.0/16"
    },
    {
      name           = "virtual-node-aci"
      address_prefix = "10.239.0.0/16"
      delegation = {
        name         = "aci-delegation"
        service_name = "Microsoft.ContainerInstance/containerGroups"
        actions      = ["Microsoft.Network/virtualNetworks/subnets/action"]
      }
    },
    {
      name           = "ingress-appgateway-subnet"
      address_prefix = "10.225.0.0/16"
      delegation = {
        name         = "app-gateway-delegation"
        service_name = "Microsoft.ServiceNetworking/trafficControllers"
        actions      = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
      }
    }
  ]

  tags = var.tags
}

# Storage Account Module
module "storage" {
  source = "../../modules/storage"

  storage_account_name         = var.storage_account_name
  resource_group_name          = azurerm_resource_group.main.name
  location                     = var.storage_location
  account_tier                 = "Standard"
  account_replication_type     = "RAGRS"
  account_kind                 = "StorageV2"
  access_tier                  = "Hot"
  enable_https_traffic_only    = true
  min_tls_version              = "TLS1_2"
  allow_nested_items_to_be_public = true
  shared_access_key_enabled    = true

  tags = var.tags
}

# ACR Module
module "acr" {
  source = "../../modules/acr"

  registry_name       = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = "eastasia"  # ACR is in eastasia
  sku                 = "Standard"
  admin_enabled       = true  # Admin is enabled on actual ACR
  tags                = var.tags
}

# Managed Identity for ESO
module "eso_identity" {
  source = "../../modules/managed-identity"

  identity_name             = var.eso_identity_name
  resource_group_name       = azurerm_resource_group.main.name
  location                  = azurerm_resource_group.main.location
  keyvault_id               = module.keyvault.keyvault_id
  enable_workload_identity  = true
  aks_oidc_issuer_url       = module.aks.oidc_issuer_url
  kubernetes_namespace      = "sentifinance"
  kubernetes_service_account = "external-secrets-sa"
  tags                      = var.tags

  depends_on = [module.aks, module.keyvault]
}

# Additional Managed Identity
module "additional_identity" {
  source = "../../modules/managed-identity"

  identity_name       = var.additional_identity_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = var.tags
}

# AKS Module
module "aks" {
  source = "../../modules/aks"

  cluster_name        = var.aks_cluster_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "${var.project_name}-aks"
  kubernetes_version  = "1.32.7"  # Actual version
  acr_id              = module.acr.registry_id
  vnet_subnet_id      = module.vnet.subnet_ids["default"]
  tags                = var.tags

  depends_on = [module.acr, module.vnet]
}

# Application Gateway for Containers
module "app_gateway" {
  source = "../../modules/app-gateway-containers"

  traffic_controller_name = var.app_gateway_name
  resource_group_id       = azurerm_resource_group.main.id
  location                = azurerm_resource_group.main.location
  subnet_id               = module.vnet.subnet_ids["ingress-appgateway-subnet"]
  tags                    = var.tags

  depends_on = [module.vnet]
}

# Key Vault Module
module "keyvault" {
  source = "../../modules/keyvault"

  keyvault_name       = var.keyvault_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

# PostgreSQL Module
# NOTE: PostgreSQL is in a SEPARATE subscription - this module is for documentation only
# The actual database connection string is stored in Azure Key Vault
# If you need to recreate the database, uncomment this module and provide correct subscription details
#
# module "postgresql" {
#   source = "../../modules/postgresql"
#
#   server_name         = var.postgresql_server_name
#   resource_group_name = azurerm_resource_group.main.name
#   location            = azurerm_resource_group.main.location
#   admin_username      = "sentiadmin"
#   admin_password      = "PLACEHOLDER"  # Store in Key Vault
#   database_name       = "postgres"
#   tags                = var.tags
# }
#
# Connection string format:
# postgresql+psycopg2://user:password@psql-sentifinance-dev.postgres.database.azure.com:5432/postgres
