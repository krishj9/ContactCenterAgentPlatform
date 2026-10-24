variable "env" {
  description = "Target deployment environment (dev, staging, prod)"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_number" {
  description = "GCP Project Number"
  type        = string
}

variable "access_policy_id" {
  description = "Access Context Manager policy ID"
  type        = string
}

variable "trusted_ip_subnetworks" {
  description = "List of trusted IP CIDR blocks permitted to access perimeter services"
  type        = list(string)
  default     = []
}

variable "authorized_service_accounts" {
  description = "List of service account principals allowed through the perimeter"
  type        = list(string)
  default     = []
}
