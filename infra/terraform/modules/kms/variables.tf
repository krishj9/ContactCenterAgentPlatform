variable "env" {
  description = "Target deployment environment (dev, staging, prod)"
  type        = string
}

variable "region" {
  description = "GCP deployment region"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_number" {
  description = "GCP Project Number"
  type        = string
}
