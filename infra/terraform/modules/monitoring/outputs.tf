output "dashboard_id" {
  description = "Cloud Monitoring Dashboard ID."
  value       = google_monitoring_dashboard.slo_dashboard.id
}

output "latency_alert_policy_id" {
  description = "Alert Policy ID for recommendation latency."
  value       = google_monitoring_alert_policy.recommendation_latency_alert.id
}

output "uptime_check_id" {
  description = "Uptime Check Config ID."
  value       = google_monitoring_uptime_check_config.api_uptime_check.id
}
