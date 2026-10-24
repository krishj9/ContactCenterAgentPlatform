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

variable "vpc_id" {
  description = "Authorized VPC network ID."
  type        = string
}

variable "memory_size_gb" {
  description = "Redis memory size in GB."
  type        = number
  default     = 1
}

variable "psa_connection" {
  description = "PSA peering connection dependency."
  type        = any
}
