variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region."
  type        = string
}

variable "repository_id" {
  description = "Artifact Registry repository ID."
  type        = string
  default     = "cc-platform-docker"
}
