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
  description = "VPC network ID for private IP access."
  type        = string
}

variable "psa_connection" {
  description = "PSA peering connection dependency."
  type        = any
}

variable "tier" {
  description = "Cloud SQL machine tier."
  type        = string
  default     = "db-custom-2-7680"
}

variable "db_password" {
  description = "Application database user password."
  type        = string
  sensitive   = true
}
