# 1. Cloud Armor Security Policy
resource "google_compute_security_policy" "armor_policy" {
  name        = "cc-armor-${var.environment}"
  description = "Cloud Armor WAF and rate limiting policy"
  project     = var.project_id

  # Rule 1: Adaptive rate limiting (1000 requests per 60 seconds)
  rule {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 1000
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
    description = "Rate limit clients exceeding 1000 requests/minute"
  }

  # Rule 2: SQLi preconfigured rule
  rule {
    action   = "deny(403)"
    priority = "2000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "Block OWASP SQL injection attacks"
  }

  # Rule 3: XSS preconfigured rule
  rule {
    action   = "deny(403)"
    priority = "3000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "Block OWASP Cross-Site Scripting (XSS) attacks"
  }

  # Default rule: Allow traffic
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }
}

# 2. Serverless NEG for Cloud Run API
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  name                  = "cc-api-neg-${var.environment}"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = var.cloud_run_service_name
  }
}

# 3. Public Backend Service (Guarded by Cloud Armor)
resource "google_compute_backend_service" "public_backend" {
  name                  = "cc-public-backend-${var.environment}"
  project               = var.project_id
  protocol              = "HTTPS"
  port_name             = "http"
  timeout_sec           = 3600 # WebSocket 1-hour session timeout
  security_policy       = google_compute_security_policy.armor_policy.id
  enable_cdn            = false

  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg.id
  }
}

# 4. Agent Backend Service (Protected by IAP)
resource "google_compute_backend_service" "agent_iap_backend" {
  name                  = "cc-agent-iap-backend-${var.environment}"
  project               = var.project_id
  protocol              = "HTTPS"
  port_name             = "http"
  timeout_sec           = 3600
  security_policy       = google_compute_security_policy.armor_policy.id

  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg.id
  }

  dynamic "iap" {
    for_each = var.enable_iap ? [1] : []
    content {
      oauth2_client_id     = var.iap_oauth2_client_id
      oauth2_client_secret = var.iap_oauth2_client_secret
    }
  }
}

# 5. URL Map with Path-Based Routing (Agent routes vs Customer/Public API routes)
resource "google_compute_url_map" "url_map" {
  name            = "cc-url-map-${var.environment}"
  project         = var.project_id
  default_service = google_compute_backend_service.public_backend.id

  host_rule {
    hosts        = ["*"]
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_service.public_backend.id

    path_rule {
      paths   = ["/agent*", "/api/v1/agent*"]
      service = google_compute_backend_service.agent_iap_backend.id
    }

    path_rule {
      paths   = ["/customer*", "/api/*", "/ws/*", "/health"]
      service = google_compute_backend_service.public_backend.id
    }
  }
}

# 6. Global Forwarding Rule and Target HTTP Proxy
resource "google_compute_global_forwarding_rule" "http_forwarding_rule" {
  name       = "cc-http-rule-${var.environment}"
  project    = var.project_id
  target     = google_compute_target_http_proxy.http_proxy.id
  port_range = "80"
}

resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "cc-http-proxy-${var.environment}"
  project = var.project_id
  url_map = google_compute_url_map.url_map.id
}
