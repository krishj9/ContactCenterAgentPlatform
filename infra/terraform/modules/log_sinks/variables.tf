variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment identifier (dev, staging, prod)."
  type        = string
  default     = "prod"
}

variable "retention_days" {
  description = "Retention period in days for locked compliance audit logs."
  type        = number
  default     = 365
}
