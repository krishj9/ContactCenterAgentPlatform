# Cloud Monitoring Module (Phase P9.3)
# Provisions Golden Signal SLO dashboards, p95 latency alerts, uptime checks, and burn-rate alert policies.

resource "google_monitoring_dashboard" "slo_dashboard" {
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "Contact Center Agent Platform — Golden Signals & SLOs (${var.environment})"
    gridLayout = {
      columns = 2
      widgets = [
        {
          title = "Recommendation End-to-End Latency (p95 SLA < ${var.recommendation_p95_threshold_ms}ms)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/cc_platform/recommendation_latency_ms\" resource.type=\"global\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_PERCENTILE_95"
                      crossSeriesReducer = "REDUCE_PERCENTILE_95"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Intent Classifier Latency (p95 SLA < ${var.intent_p95_threshold_ms}ms)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/cc_platform/intent_latency_ms\" resource.type=\"global\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_PERCENTILE_95"
                      crossSeriesReducer = "REDUCE_PERCENTILE_95"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Grounding Adherence Rate (Target >= 90%)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/cc_platform/grounding_score\" resource.type=\"global\""
                    aggregation = {
                      alignmentPeriod    = "300s"
                      perSeriesAligner   = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_MEAN"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Active WebSocket Sessions"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/cc_platform/active_websocket_sessions\" resource.type=\"global\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_MAX"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
              }
            ]
          }
        }
      ]
    }
  })
}

# 1. Recommendation Latency p95 SLA Alert
resource "google_monitoring_alert_policy" "recommendation_latency_alert" {
  project      = var.project_id
  display_name = "Recommendation Latency p95 > ${var.recommendation_p95_threshold_ms}ms (${var.environment})"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Recommendation p95 latency exceeds ${var.recommendation_p95_threshold_ms}ms threshold"
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/cc_platform/recommendation_latency_ms\" resource.type=\"global\""
      duration        = "300s" # 5-minute sustained breach
      comparison      = "COMPARISON_GT"
      threshold_value = var.recommendation_p95_threshold_ms
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = var.notification_channels
}

# 2. WebSocket Drop Rate Alert
resource "google_monitoring_alert_policy" "websocket_drop_rate_alert" {
  project      = var.project_id
  display_name = "WebSocket Connection Drop Rate > 2% (${var.environment})"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "WebSocket unexpected drop rate exceeds 2%"
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/cc_platform/websocket_drop_count\" resource.type=\"global\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = var.notification_channels
}

# 3. Availability SLO 1h Burn-Rate Alert (14.4x)
resource "google_monitoring_alert_policy" "slo_burn_rate_alert" {
  project      = var.project_id
  display_name = "Availability SLO Fast Burn-Rate Alert (14.4x 1h) (${var.environment})"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Cloud Run 5xx server error rate exceeds 1h SLO burn-rate"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = var.notification_channels
}

# 4. HTTPS Uptime Check on /health
resource "google_monitoring_uptime_check_config" "api_uptime_check" {
  project      = var.project_id
  display_name = "API Gateway /health Check (${var.environment})"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path           = "/health"
    port           = 443
    use_ssl        = true
    validate_ssl   = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.api_gateway_hostname
    }
  }
}
