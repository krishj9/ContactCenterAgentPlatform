variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "environment" {
  description = "Environment identifier (staging, prod)."
  type        = string
  default     = "staging"
}

variable "enforce" {
  description = "Whether to strictly block unsigned images (true) or dry-run audit log (false)."
  type        = bool
  default     = true
}

variable "evaluation_mode" {
  description = "Binary Authorization admission evaluation mode."
  type        = string
  default     = "REQUIRE_ATTESTATION"
}

variable "service_account_email" {
  description = "Service account email of Cloud Run deployments for IAM bindings."
  type        = string
  default     = ""
}
