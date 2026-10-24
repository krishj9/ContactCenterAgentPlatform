variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "network_id" {
  description = "Optional VPC Network ID for private endpoint."
  type        = string
  default     = null
}
