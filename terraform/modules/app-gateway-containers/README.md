# Application Gateway for Containers Module

This module manages Azure Application Gateway for Containers (Traffic Controller).

## Important Note

Application Gateway for Containers is a **NEW** service from Azure, different from the classic Application Gateway. It uses the `Microsoft.ServiceNetworking/trafficControllers` resource type.

This module uses the `azapi` provider because the `azurerm` provider doesn't yet have full support for this new service.

## Requirements

Add this to your `terraform` block:

```hcl
required_providers {
  azapi = {
    source  = "azure/azapi"
    version = "~> 1.9.0"
  }
}
```

And configure the provider:

```hcl
provider "azapi" {
}
```

## Usage

```hcl
module "app_gateway" {
  source = "../../modules/app-gateway-containers"

  traffic_controller_name = "sentifinance-app-gateway"
  resource_group_id       = azurerm_resource_group.main.id
  location                = "southeastasia"
  subnet_id               = module.vnet.subnet_ids["ingress-appgateway-subnet"]

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

## Resources Created

- `Microsoft.ServiceNetworking/trafficControllers` - Traffic Controller
- `Microsoft.ServiceNetworking/trafficControllers/associations` - Subnet association (optional)

## Documentation

- [Application Gateway for Containers Overview](https://learn.microsoft.com/en-us/azure/application-gateway/for-containers/overview)
- [azapi Provider Documentation](https://registry.terraform.io/providers/azure/azapi/latest/docs)
