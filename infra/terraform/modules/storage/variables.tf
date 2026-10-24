variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region."
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "kms_key_name" {
  description = "Optional Cloud KMS key name for CMEK."
  type        = string
  default     = null
}
