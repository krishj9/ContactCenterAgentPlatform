/**
 * Cloud KMS Customer-Managed Encryption Keys (CMEK) Module (Spec §6.1, Phase P10.2).
 *
 * Provisions KMS Key Rings and distinct CryptoKeys with automated 90-day rotation
 * for Cloud SQL, Cloud Storage, Vertex AI, and BigQuery.
 */

resource "google_kms_key_ring" "keyring" {
  name     = "cc-keyring-${var.env}-${var.region}"
  location = var.region
  project  = var.project_id
}

# 1. Cloud SQL CMEK Key
resource "google_kms_crypto_key" "sql_key" {
  name            = "cc-sql-key-${var.env}"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key_iam_member" "sql_sa_encrypter_decrypter" {
  crypto_key_id = google_kms_crypto_key.sql_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${var.project_number}@gcp-sa-cloud-sql.iam.gserviceaccount.com"
}

# 2. Cloud Storage CMEK Key
resource "google_kms_crypto_key" "storage_key" {
  name            = "cc-storage-key-${var.env}"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key_iam_member" "storage_sa_encrypter_decrypter" {
  crypto_key_id = google_kms_crypto_key.storage_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${var.project_number}@gs-project-accounts.iam.gserviceaccount.com"
}

# 3. Vertex AI CMEK Key
resource "google_kms_crypto_key" "vertex_key" {
  name            = "cc-vertex-key-${var.env}"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key_iam_member" "vertex_sa_encrypter_decrypter" {
  crypto_key_id = google_kms_crypto_key.vertex_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${var.project_number}@gcp-sa-aiplatform.iam.gserviceaccount.com"
}

# 4. BigQuery CMEK Key
resource "google_kms_crypto_key" "bigquery_key" {
  name            = "cc-bigquery-key-${var.env}"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key_iam_member" "bigquery_sa_encrypter_decrypter" {
  crypto_key_id = google_kms_crypto_key.bigquery_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:bq-${var.project_number}@bigquery-encryption.iam.gserviceaccount.com"
}
