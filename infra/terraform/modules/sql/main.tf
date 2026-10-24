# Cloud SQL PostgreSQL 16 Instance with pgvector & IAM Auth
resource "google_sql_database_instance" "instance" {
  name                = "cc-sql-${var.environment}"
  project             = var.project_id
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = var.environment == "prod"

  settings {
    tier              = var.tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = 20
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.vpc_id
      enable_private_path_for_google_cloud_services = true
    }

    # Enable pgvector and IAM authentication flags
    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
    }
  }

  depends_on = [var.psa_connection]
}

resource "google_sql_database" "database" {
  name     = "cc_platform"
  instance = google_sql_database_instance.instance.name
  project  = var.project_id
}

resource "google_sql_user" "app_user" {
  name     = "cc_app"
  instance = google_sql_database_instance.instance.name
  project  = var.project_id
  password = var.db_password
}
