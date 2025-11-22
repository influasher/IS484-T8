variable "vnet_name" {
  description = "Virtual network name"
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

variable "address_space" {
  description = "Virtual network address space (CIDR blocks)"
  type        = list(string)
}

variable "subnets" {
  description = "List of subnets to create"
  type = list(object({
    name           = string
    address_prefix = string
    service_endpoints = optional(list(string), [])
    delegation = optional(object({
      name         = string
      service_name = string
      actions      = optional(list(string), [])
    }))
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to virtual network"
  type        = map(string)
  default     = {}
}
