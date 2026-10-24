output "endpoint_id" {
  value = google_vertex_ai_endpoint.endpoint.name
}

output "endpoint_resource_name" {
  value = "projects/${var.project_id}/locations/${var.region}/endpoints/${google_vertex_ai_endpoint.endpoint.name}"
}
