output "perimeter_name" {
  description = "Resource name of the created VPC-SC service perimeter"
  value       = google_access_context_manager_service_perimeter.cc_service_perimeter.name
}

output "access_level_name" {
  description = "Resource name of the perimeter access level"
  value       = google_access_context_manager_access_level.perimeter_access_level.name
}
