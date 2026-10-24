/**
 * VPC Service Controls (VPC-SC) Module (Spec §6.1, Phase P10.1).
 *
 * Defines the cryptographic security perimeter enclosing all data, ML, and API services:
 * Cloud Run, Cloud SQL, Vertex AI, Cloud Storage, and BigQuery.
 */

resource "google_access_context_manager_access_level" "perimeter_access_level" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/accessLevels/${var.env}_cc_trusted_access"
  title  = "${var.env} Contact Center Trusted Access Level"

  basic {
    conditions {
      ip_subnetworks = var.trusted_ip_subnetworks

      members = var.authorized_service_accounts
    }
  }
}

resource "google_access_context_manager_service_perimeter" "cc_service_perimeter" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/${var.env}_cc_perimeter"
  title  = "${var.env} Contact Center Secure Perimeter"

  status {
    restricted_services = [
      "run.googleapis.com",
      "sqladmin.googleapis.com",
      "aiplatform.googleapis.com",
      "storage.googleapis.com",
      "bigquery.googleapis.com",
      "secretmanager.googleapis.com",
      "cloudkms.googleapis.com",
      "dlp.googleapis.com",
    ]

    resources = [
      "projects/${var.project_number}",
    ]

    access_levels = [
      google_access_context_manager_access_level.perimeter_access_level.name,
    ]

    # Ingress policy allowing CI/CD and authorized dev networks
    ingress_policies {
      ingress_from {
        identity_type = "ANY_IDENTITY"
        sources {
          access_level = google_access_context_manager_access_level.perimeter_access_level.name
        }
      }
      ingress_to {
        resources = ["*"]
        operations {
          service_name = "*"
          method_selectors {
            method = "*"
          }
        }
      }
    }

    # Egress policy allowing controlled access to external auditable endpoints
    egress_policies {
      egress_from {
        identity_type = "ANY_IDENTITY"
      }
      egress_to {
        resources = ["*"]
        operations {
          service_name = "storage.googleapis.com"
          method_selectors {
            method = "*"
          }
        }
      }
    }
  }

  use_explicit_dry_run_spec = false
}
