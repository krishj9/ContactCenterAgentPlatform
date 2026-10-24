output "keyring_id" {
  description = "ID of the KMS Key Ring"
  value       = google_kms_key_ring.keyring.id
}

output "sql_crypto_key_id" {
  description = "ID of the Cloud SQL CMEK CryptoKey"
  value       = google_kms_crypto_key.sql_key.id
}

output "storage_crypto_key_id" {
  description = "ID of the Cloud Storage CMEK CryptoKey"
  value       = google_kms_crypto_key.storage_key.id
}

output "vertex_crypto_key_id" {
  description = "ID of the Vertex AI CMEK CryptoKey"
  value       = google_kms_crypto_key.vertex_key.id
}

output "bigquery_crypto_key_id" {
  description = "ID of the BigQuery CMEK CryptoKey"
  value       = google_kms_crypto_key.bigquery_key.id
}
