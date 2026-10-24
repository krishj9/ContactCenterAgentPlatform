locals {
  buckets = {
    raw       = "raw",
    processed = "processed",
    models    = "models",
    eval      = "eval",
  }
}

resource "google_storage_bucket" "buckets" {
  for_each = locals.buckets

  name                        = "${var.project_id}-${var.environment}-${each.value}"
  project                     = var.project_id
  location                    = var.region
  force_destroy               = var.environment == "dev"
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  dynamic "encryption" {
    for_each = var.kms_key_name != null ? [var.kms_key_name] : []
    content {
      default_kms_key_name = encryption.value
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 3
      with_state         = "ARCHIVED"
    }
  }
}
