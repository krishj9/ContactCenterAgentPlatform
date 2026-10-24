# 1. API Gateway Service Account
resource "google_service_account" "sa_api" {
  account_id   = "sa-api-${var.environment}"
  display_name = "Cloud Run API Gateway (${var.environment})"
  project      = var.project_id
}

# 2. Intent Service / Model Endpoint Service Account
resource "google_service_account" "sa_intent" {
  account_id   = "sa-intent-${var.environment}"
  display_name = "Vertex AI Intent Classifier (${var.environment})"
  project      = var.project_id
}

# 3. Pipeline & Batch Ingest Service Account
resource "google_service_account" "sa_pipeline" {
  account_id   = "sa-pipeline-${var.environment}"
  display_name = "ML & Knowledge Base Pipelines (${var.environment})"
  project      = var.project_id
}

# IAM Bindings for sa-api:
# - Cloud SQL Client
# - Vertex AI User
# - Secret Manager Secret Accessor
# - Speech Client
resource "google_project_iam_member" "api_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.sa_api.email}"
}

resource "google_project_iam_member" "api_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.sa_api.email}"
}

resource "google_project_iam_member" "api_speech" {
  project = var.project_id
  role    = "roles/speech.client"
  member  = "serviceAccount:${google_service_account.sa_api.email}"
}

resource "google_project_iam_member" "api_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.sa_api.email}"
}

# IAM Bindings for sa-pipeline:
resource "google_project_iam_member" "pipeline_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.sa_pipeline.email}"
}

resource "google_project_iam_member" "pipeline_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.sa_pipeline.email}"
}

resource "google_project_iam_member" "pipeline_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.sa_pipeline.email}"
}
