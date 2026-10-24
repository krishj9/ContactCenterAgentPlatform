variable "project_id" {
  description = "GCP Project ID for Prod environment."
  type        = string
}

variable "region" {
  description = "GCP Region."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment identifier."
  type        = string
  default     = "prod"
}

variable "api_image" {
  description = "Container image for Cloud Run API."
  type        = string
  default     = "us-central1-docker.pkg.dev/sample-project-prod/cc-platform-docker/api:latest"
}

variable "db_password" {
  description = "Database user password."
  type        = string
  sensitive   = true
  default     = "ChangeMeProdUltraSecurePass789!"
}

variable "canary_revision" {
  description = "Optional revision name for canary routing."
  type        = string
  default     = null
}

variable "canary_percent" {
  description = "Percentage of traffic routed to canary revision (0-100)."
  type        = number
  default     = 0
}

variable "enable_binary_authorization" {
  description = "Strictly enforce Binary Authorization signatures."
  type        = bool
  default     = true
}

variable "enable_iap" {
  description = "Enable Identity-Aware Proxy guarding /agent routes."
  type        = bool
  default     = true
}
