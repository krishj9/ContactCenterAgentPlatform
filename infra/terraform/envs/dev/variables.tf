variable "project_id" {
  description = "GCP Project ID for Dev environment."
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
  default     = "dev"
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
  default     = "ChangeMeDevSecurePass123!"
}
