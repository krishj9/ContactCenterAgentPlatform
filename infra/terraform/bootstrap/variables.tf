variable "project_id" {
  description = "The GCP Project ID to bootstrap."
  type        = string
}

variable "region" {
  description = "Primary GCP region for resources."
  type        = string
  default     = "us-central1"
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo' for Workload Identity Federation."
  type        = string
  default     = "krishj9/ContactCenterAgentPlatform"
}
