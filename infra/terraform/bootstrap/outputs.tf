output "tfstate_bucket" {
  description = "Name of GCS bucket for remote Terraform state."
  value       = google_storage_bucket.tf_state.name
}

output "artifact_registry_id" {
  description = "ID of Docker artifact registry repository."
  value       = google_artifact_registry_repository.docker_repo.name
}

output "artifact_registry_url" {
  description = "Image path prefix for Docker images."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "wif_provider_name" {
  description = "Workload Identity Provider resource name for GitHub Actions."
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "deployer_service_account_email" {
  description = "Service account email for GitHub Actions deployment."
  value       = google_service_account.github_deployer.email
}
