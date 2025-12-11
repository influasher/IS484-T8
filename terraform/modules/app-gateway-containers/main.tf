# Application Gateway for Containers (Traffic Controller)
# Note: This is the new Azure Application Gateway for Containers service,
# not the classic Application Gateway resource.
# Provider: Microsoft.ServiceNetworking/trafficControllers

resource "azapi_resource" "traffic_controller" {
  type      = "Microsoft.ServiceNetworking/trafficControllers@2023-11-01"
  name      = var.traffic_controller_name
  parent_id = var.resource_group_id
  location  = var.location

  body = jsonencode({
    properties = {}
  })

  tags = var.tags
}

# Association with subnet
resource "azapi_resource" "association" {
  count     = var.subnet_id != null ? 1 : 0
  type      = "Microsoft.ServiceNetworking/trafficControllers/associations@2023-11-01"
  name      = "${var.traffic_controller_name}-association"
  parent_id = azapi_resource.traffic_controller.id

  body = jsonencode({
    properties = {
      associationType = "subnets"
      subnet = {
        id = var.subnet_id
      }
    }
  })

  depends_on = [azapi_resource.traffic_controller]
}
