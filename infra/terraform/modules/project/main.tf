locals {
  services = distinct(concat([
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "speech.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "discoveryengine.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "iap.googleapis.com",
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
  ], var.extra_services))
}

resource "google_project_service" "apis" {
  for_each = toset(locals.services)

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}
