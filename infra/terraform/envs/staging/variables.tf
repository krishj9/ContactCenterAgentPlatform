variable "project_id" {
  description = "GCP Project ID for Staging environment."
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
  default     = "staging"
}

variable "api_image" {
  description = "Container image for Cloud Run API."
  type        = string
  default     = "us-central1-docker.pkg.dev/sample-project/cc-platform-docker/api:latest"
}

variable "db_password" {
  description = "Database user password."
  type        = string
  sensitive   = true
  default     = "ChangeMeStagingSecurePass456!"
}

variable "enable_binary_authorization" {
  description = "Enforce cryptographic image signatures on Staging."
  type        = bool
  default     = true
}
