output "api_service_uri" {
  value = module.cloud_run_service.uri
}

output "load_balancer_ip" {
  value = module.lb_armor_iap.load_balancer_ip
}

output "firebase_hosting_url" {
  value = module.firebase.default_url
}

output "cloud_sql_connection_name" {
  value = module.sql.instance_connection_name
}

output "redis_host" {
  value = module.redis.host
}

output "vertex_endpoint_id" {
  value = module.vertex_endpoint.endpoint_id
}
