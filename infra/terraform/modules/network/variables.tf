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

variable "subnet_cidr" {
  description = "Primary subnet CIDR range."
  type        = string
  default     = "10.10.0.0/20"
}

variable "connector_cidr" {
  description = "Serverless VPC Access connector CIDR range."
  type        = string
  default     = "10.10.16.0/28"
}
