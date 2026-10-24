# Cloud Scheduler Module (Phase P8.4)
# Configures automated cron schedules for monthly intent retraining, weekly KB sync, and nightly eval.

resource "google_cloud_scheduler_job" "monthly_intent_retrain" {
  name             = "cc-intent-retrain-${var.environment}"
  description      = "Monthly automated trigger for Gemma 3 LoRA intent classifier retraining pipeline"
  schedule         = var.intent_retrain_schedule
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"
  project          = var.project_id
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "${var.api_gateway_url}/v1/pipelines/intent/train"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({
      environment = var.environment
      trigger     = "cloud-scheduler-monthly"
      taxonomy    = "taxonomy/intents.yaml"
    }))

    oidc_token {
      service_account_email = var.service_account_email
      audience              = var.api_gateway_url
    }
  }
}

resource "google_cloud_scheduler_job" "weekly_kb_sync" {
  name             = "cc-kb-sync-${var.environment}"
  description      = "Weekly knowledge base health check and policy corpus synchronization"
  schedule         = var.kb_sync_schedule
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"
  project          = var.project_id
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "${var.api_gateway_url}/v1/pipelines/kb/sync"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({
      environment = var.environment
      trigger     = "cloud-scheduler-weekly"
    }))

    oidc_token {
      service_account_email = var.service_account_email
      audience              = var.api_gateway_url
    }
  }
}

resource "google_cloud_scheduler_job" "nightly_eval" {
  name             = "cc-nightly-eval-${var.environment}"
  description      = "Daily E2E replay evaluation and golden scenario quality measurement"
  schedule         = var.nightly_eval_schedule
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"
  project          = var.project_id
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "${var.api_gateway_url}/v1/eval/nightly"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({
      environment = var.environment
      trigger     = "cloud-scheduler-daily"
    }))

    oidc_token {
      service_account_email = var.service_account_email
      audience              = var.api_gateway_url
    }
  }
}
