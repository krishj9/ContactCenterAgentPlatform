output "sa_api_email" {
  value = google_service_account.sa_api.email
}

output "sa_intent_email" {
  value = google_service_account.sa_intent.email
}

output "sa_pipeline_email" {
  value = google_service_account.sa_pipeline.email
}
