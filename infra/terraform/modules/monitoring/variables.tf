variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "environment" {
  description = "Environment identifier (dev, staging, prod)."
  type        = string
  default     = "prod"
}

variable "api_gateway_hostname" {
  description = "Hostname for Cloud Run API / Load Balancer uptime checks."
  type        = string
  default     = "api.ccplatform.internal"
}

variable "notification_channels" {
  description = "List of Cloud Monitoring notification channel IDs for alerting."
  type        = list(string)
  default     = []
}

variable "recommendation_p95_threshold_ms" {
  description = "SLA threshold for end-to-end recommendation p95 latency in milliseconds."
  type        = number
  default     = 2500
}

variable "intent_p95_threshold_ms" {
  description = "SLA threshold for intent classifier p95 latency in milliseconds."
  type        = number
  default     = 60
}
