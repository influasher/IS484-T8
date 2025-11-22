variable "traffic_controller_name" {
  description = "Traffic controller (Application Gateway for Containers) name"
  type        = string
}

variable "resource_group_id" {
  description = "Resource group ID (full Azure resource ID)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for association (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to traffic controller"
  type        = map(string)
  default     = {}
}
