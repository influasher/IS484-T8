variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "dns_prefix" {
  description = "DNS prefix for the cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.32.7"
}

variable "default_node_pool_name" {
  description = "Default node pool name"
  type        = string
  default     = "agentpool"
}

variable "node_count" {
  description = "Initial node count"
  type        = number
  default     = 4
}

variable "vm_size" {
  description = "VM size for nodes"
  type        = string
  default     = "Standard_D2lds_v6"
}

variable "enable_auto_scaling" {
  description = "Enable autoscaling"
  type        = bool
  default     = true
}

variable "min_count" {
  description = "Minimum node count for autoscaling"
  type        = number
  default     = 3
}

variable "max_count" {
  description = "Maximum node count for autoscaling"
  type        = number
  default     = 5
}

variable "vnet_subnet_id" {
  description = "VNet subnet ID for node pool"
  type        = string
  default     = null
}

variable "availability_zones" {
  description = "Availability zones for node pool"
  type        = list(string)
  default     = ["2", "3"]
}

variable "os_disk_size_gb" {
  description = "OS disk size in GB"
  type        = number
  default     = 128
}

variable "network_plugin" {
  description = "Network plugin (azure or kubenet)"
  type        = string
  default     = "azure"
}

variable "network_policy" {
  description = "Network policy (none, calico, azure)"
  type        = string
  default     = "none"
}

variable "service_cidr" {
  description = "Service CIDR for Kubernetes services"
  type        = string
  default     = "10.0.0.0/16"
}

variable "dns_service_ip" {
  description = "DNS service IP (must be within service_cidr)"
  type        = string
  default     = "10.0.0.10"
}

variable "network_data_plane" {
  description = "Network data plane (azure or cilium)"
  type        = string
  default     = "azure"
}

variable "acr_id" {
  description = "ACR resource ID for role assignment"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
