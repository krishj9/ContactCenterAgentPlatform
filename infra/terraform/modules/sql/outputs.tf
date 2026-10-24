output "instance_name" {
  value = google_sql_database_instance.instance.name
}

output "instance_connection_name" {
  value = google_sql_database_instance.instance.connection_name
}

output "private_ip_address" {
  value = google_sql_database_instance.instance.private_ip_address
}

output "database_name" {
  value = google_sql_database.database.name
}

output "db_user" {
  value = google_sql_user.app_user.name
}
