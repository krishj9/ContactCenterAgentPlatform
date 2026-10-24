resource "google_redis_instance" "redis" {
  name           = "cc-redis-${var.environment}"
  project        = var.project_id
  region         = var.region
  tier           = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb = var.memory_size_gb

  authorized_network = var.vpc_id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  transit_encryption_mode = "SERVER_AUTHENTICATION"
  auth_enabled            = true

  redis_version = "REDIS_7_0"

  depends_on = [var.psa_connection]
}
