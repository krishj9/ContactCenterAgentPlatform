output "host" {
  value = google_redis_instance.redis.host
}

output "port" {
  value = google_redis_instance.redis.port
}

output "auth_string" {
  value     = google_redis_instance.redis.auth_string
  sensitive = true
}

output "redis_url" {
  value     = "rediss://default:${google_redis_instance.redis.auth_string}@${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
  sensitive = true
}
