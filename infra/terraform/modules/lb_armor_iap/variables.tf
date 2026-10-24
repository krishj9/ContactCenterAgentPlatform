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

variable "cloud_run_service_name" {
  description = "Cloud Run API service name."
  type        = string
}

variable "enable_iap" {
  description = "Enable Identity-Aware Proxy for agent routes."
  type        = bool
  default     = false
}

variable "iap_oauth2_client_id" {
  description = "OAuth2 Client ID for IAP."
  type        = string
  default     = ""
}

variable "iap_oauth2_client_secret" {
  description = "OAuth2 Client Secret for IAP."
  type        = string
  default     = ""
  sensitive   = true
}
