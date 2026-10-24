# Audit Log Sinks Module (Phase P9.4)
# Streams structured audit logs & agent feedback to BigQuery and exports immutable logs to locked GCS bucket.

# 1. BigQuery Dataset for Analytics & Agent Feedback
resource "google_bigquery_dataset" "audit_dataset" {
  dataset_id  = "cc_audit_logs_${var.environment}"
  project     = var.project_id
  location    = var.region
  description = "Contact center audit event logs and agent feedback analytics dataset"

  labels = {
    environment = var.environment
    purpose     = "compliance-and-analytics"
  }
}

# 2. BigQuery Log Sink
resource "google_logging_project_sink" "bigquery_audit_sink" {
  name                   = "cc-bq-audit-sink-${var.environment}"
  project                = var.project_id
  destination            = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.audit_dataset.dataset_id}"
  filter                 = "jsonPayload.event_type != \"\" OR logName =~ \"cc_audit\" OR jsonPayload.feedback_type != \"\""
  unique_writer_identity = true
}

resource "google_project_iam_member" "bq_sink_writer" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = google_logging_project_sink.bigquery_audit_sink.writer_identity
}

# 3. Locked GCS Compliance Bucket (Object Retention Lock 1-Year)
resource "google_storage_bucket" "compliance_bucket" {
  name                        = "cc-audit-compliance-locked-${var.environment}-${var.project_id}"
  project                     = var.project_id
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  retention_policy {
    retention_period = var.retention_days * 86400 # 365 days in seconds
    is_locked        = var.environment == "prod"  # Irreversible lock in production for SEC/FINRA compliance
  }

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = var.retention_days + 30
    }
  }
}

# 4. GCS Storage Log Sink
resource "google_logging_project_sink" "gcs_compliance_sink" {
  name                   = "cc-gcs-compliance-sink-${var.environment}"
  project                = var.project_id
  destination            = "storage.googleapis.com/${google_storage_bucket.compliance_bucket.name}"
  filter                 = "logName =~ \"cc_audit\""
  unique_writer_identity = true
}

resource "google_storage_bucket_iam_member" "gcs_sink_writer" {
  bucket = google_storage_bucket.compliance_bucket.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.gcs_compliance_sink.writer_identity
}
