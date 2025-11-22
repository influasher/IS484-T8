terraform {
  backend "azurerm" {
    resource_group_name  = "sentifinance-terraform-rg"
    storage_account_name = "REPLACE_WITH_YOUR_STORAGE_ACCOUNT"  # Replace after creating storage
    container_name       = "tfstate"
    key                  = "production.tfstate"
  }
}
