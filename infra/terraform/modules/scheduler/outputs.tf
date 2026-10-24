output "monthly_intent_retrain_job_id" {
  description = "Cloud Scheduler Job ID for monthly intent retraining."
  value       = google_cloud_scheduler_job.monthly_intent_retrain.id
}

output "weekly_kb_sync_job_id" {
  description = "Cloud Scheduler Job ID for weekly KB sync."
  value       = google_cloud_scheduler_job.weekly_kb_sync.id
}

output "nightly_eval_job_id" {
  description = "Cloud Scheduler Job ID for nightly evaluation."
  value       = google_cloud_scheduler_job.nightly_eval.id
}
