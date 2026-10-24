output "policy_id" {
  description = "Binary Authorization Policy ID."
  value       = google_binary_authorization_policy.policy.id
}

output "attestor_name" {
  description = "Binary Authorization Attestor resource name."
  value       = google_binary_authorization_attestor.attestor.name
}

output "note_id" {
  description = "Container Analysis Note ID."
  value       = google_container_analysis_note.note.id
}
