resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id
}

resource "google_firebase_hosting_site" "site" {
  provider = google-beta
  project  = var.project_id
  site_id  = var.site_id != null ? var.site_id : "${var.project_id}-web"

  depends_on = [google_firebase_project.default]
}
