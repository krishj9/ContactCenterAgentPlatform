variable "project_id" {
  description = "The GCP Project ID."
  type        = string
}

variable "extra_services" {
  description = "Additional GCP APIs to enable."
  type        = list(string)
  default     = []
}
