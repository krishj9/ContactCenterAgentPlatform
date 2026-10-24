resource "google_cloud_run_v2_service" "service" {
  name     = "cc-api-${var.environment}"
  location = var.region
  project  = var.project_id

  # Session affinity for WebSocket connections
  session_affinity = true

  dynamic "binary_authorization" {
    for_each = var.enable_binary_authorization ? [1] : []
    content {
      use_default = true
    }
  }

  template {
    service_account = var.service_account_email
    timeout         = "3600s" # 1-hour WebSocket connection timeout

    scaling {
      min_instance_count = var.min_instance_count # Keep warm for zero voice cold-start latency
      max_instance_count = var.max_instance_count
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
        cpu_idle = false # Always allocate CPU for active audio processing
      }

      ports {
        container_port = 8000
      }

      env {
        name  = "CC_APP_PROFILE"
        value = "gcp"
      }

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds = 15
      }
    }
  }

  dynamic "traffic" {
    for_each = length(var.traffic) > 0 ? var.traffic : [{
      type     = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
      percent  = 100
      revision = null
      tag      = null
    }]
    content {
      type     = traffic.value.type
      percent  = traffic.value.percent
      revision = traffic.value.revision
      tag      = traffic.value.tag
    }
  }
}

# Allow public invocations if fronted by Load Balancer or Firebase proxy
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.service.location
  project  = google_cloud_run_v2_service.service.project
  service  = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
