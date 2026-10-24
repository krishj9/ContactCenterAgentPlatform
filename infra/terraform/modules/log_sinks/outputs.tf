output "bigquery_dataset_id" {
  description = "BigQuery dataset ID for audit and feedback logs."
  value       = google_bigquery_dataset.audit_dataset.dataset_id
}

output "compliance_bucket_name" {
  description = "Locked compliance GCS bucket name."
  value       = google_storage_bucket.compliance_bucket.name
}

output "bigquery_sink_writer_identity" {
  description = "Service account writer identity for BigQuery sink."
  value       = google_logging_project_sink.bigquery_audit_sink.writer_identity
}
