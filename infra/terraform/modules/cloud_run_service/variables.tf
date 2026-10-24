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

variable "image" {
  description = "Container image URL."
  type        = string
}

variable "service_account_email" {
  description = "Service account email for Cloud Run."
  type        = string
}

variable "vpc_connector_id" {
  description = "VPC Access Connector ID."
  type        = string
}

variable "env_vars" {
  description = "Key-value environment variables."
  type        = map(string)
  default     = {}
}

variable "traffic" {
  description = "Traffic allocations for canary routing and progressive rollouts."
  type = list(object({
    type     = string
    percent  = number
    revision = optional(string)
    tag      = optional(string)
  }))
  default = []
}

variable "enable_binary_authorization" {
  description = "Enforce Binary Authorization signature verification."
  type        = bool
  default     = false
}

variable "min_instance_count" {
  description = "Minimum warm instances for low latency."
  type        = number
  default     = 1
}

variable "max_instance_count" {
  description = "Maximum scaling instances."
  type        = number
  default     = 10
}
