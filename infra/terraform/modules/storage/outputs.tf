output "bucket_names" {
  description = "Map of created GCS bucket names."
  value       = { for k, b in google_storage_bucket.buckets : k => b.name }
}

output "bucket_urls" {
  description = "Map of created GCS bucket gs:// URLs."
  value       = { for k, b in google_storage_bucket.buckets : k => b.url }
}

output "models_bucket" {
  description = "Models storage bucket name."
  value       = google_storage_bucket.buckets["models"].name
}
