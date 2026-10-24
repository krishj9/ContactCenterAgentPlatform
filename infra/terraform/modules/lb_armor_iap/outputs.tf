output "load_balancer_ip" {
  value = google_compute_global_forwarding_rule.http_forwarding_rule.ip_address
}

output "security_policy_id" {
  value = google_compute_security_policy.armor_policy.id
}
