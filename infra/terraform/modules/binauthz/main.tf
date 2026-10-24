# Binary Authorization Module (Phase P8.6)
# Enforces cryptographic attestation signatures on container images deployed to Staging and Production.

resource "google_container_analysis_note" "note" {
  name    = "release-note-${var.environment}"
  project = var.project_id

  attestation_authority {
    hint {
      human_readable_name = "Release Attestor Note for ${var.environment}"
    }
  }
}

resource "google_binary_authorization_attestor" "attestor" {
  name    = "release-attestor-${var.environment}"
  project = var.project_id

  attestation_authority_note {
    note_reference = google_container_analysis_note.note.name
  }
}

resource "google_binary_authorization_policy" "policy" {
  project                       = var.project_id
  global_policy_evaluation_mode = "ENABLE"

  default_admission_rule {
    evaluation_mode         = var.evaluation_mode
    enforcement_mode        = var.enforce ? "ENFORCED_BLOCK_AND_AUDIT_LOG" : "DRYRUN_AUDIT_LOG_ONLY"
    require_attestations_by = [google_binary_authorization_attestor.attestor.name]
  }

  admission_whitelist_patterns {
    name_pattern = "gcr.io/google-containers/*"
  }

  admission_whitelist_patterns {
    name_pattern = "gke.gcr.io/*"
  }

  admission_whitelist_patterns {
    name_pattern = "*-docker.pkg.dev/cloud-run-internal/*"
  }
}

resource "google_container_analysis_note_iam_member" "note_viewer" {
  count   = var.service_account_email != "" ? 1 : 0
  project = var.project_id
  note    = google_container_analysis_note.note.name
  role    = "roles/containeranalysis.notes.viewer"
  member  = "serviceAccount:${var.service_account_email}"
}
