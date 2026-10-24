variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "site_id" {
  description = "Firebase Hosting custom site ID."
  type        = string
  default     = null
}
