variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Scheduler."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment identifier (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "service_account_email" {
  description = "Service account email for Cloud Scheduler OIDC/OAuth authentication."
  type        = string
}

variable "intent_retrain_schedule" {
  description = "Cron schedule for monthly intent model retraining."
  type        = string
  default     = "0 2 1 * *"
}

variable "kb_sync_schedule" {
  description = "Cron schedule for weekly knowledge base integrity check and sync."
  type        = string
  default     = "0 3 * * 0"
}

variable "nightly_eval_schedule" {
  description = "Cron schedule for daily E2E and golden evaluation run."
  type        = string
  default     = "0 4 * * *"
}

variable "api_gateway_url" {
  description = "Target API Gateway URL for trigger endpoints."
  type        = string
  default     = "https://api.ccplatform.internal"
}
