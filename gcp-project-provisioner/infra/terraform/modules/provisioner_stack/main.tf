# Core infrastructure for the provisioner: Artifact Registry, Cloud Run Job,
# Cloud Scheduler, the two service accounts it needs, and Secret Manager for
# the Freshservice API key. No secret values live in this repo — the API
# key is uploaded out-of-band (see INTERN_GUIDE.md Phase 7) directly into
# Secret Manager.

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

locals {
  runtime_sa_id    = "${var.name_prefix}-sa"
  cloudbuild_sa_id = "${var.name_prefix}-build-sa"
  secret_id        = "${var.name_prefix}-fs-api-key"
  ar_repo_id       = "gcp-provisioner"
  job_name         = "${var.name_prefix}-job"
  scheduler_id     = "${var.name_prefix}-scheduler"
}

data "google_project" "current" {
  project_id = var.project_id
}

# ---------------------------------------------------------------------------
# Enable required APIs
# ---------------------------------------------------------------------------
resource "google_project_service" "required" {
  for_each = toset([
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
  ])
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ---------------------------------------------------------------------------
# Artifact Registry
# ---------------------------------------------------------------------------
resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.region
  repository_id = local.ar_repo_id
  format        = "DOCKER"
  description   = "Container images for the GCP project provisioner job."

  depends_on = [google_project_service.required]
}

# ---------------------------------------------------------------------------
# Service accounts
# ---------------------------------------------------------------------------
resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = local.runtime_sa_id
  display_name = "GCP Project Provisioner - runtime"
}

resource "google_service_account" "cloudbuild" {
  project      = var.project_id
  account_id   = local.cloudbuild_sa_id
  display_name = "GCP Project Provisioner - Cloud Build"
}

resource "google_project_iam_member" "cloudbuild_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

resource "google_project_iam_member" "cloudbuild_logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

resource "google_project_iam_member" "runtime_logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# NOTE: roles/resourcemanager.projectCreator and projectIamAdmin on the
# destination FOLDER cannot be granted from this project's Terraform state —
# folder IAM must be granted by someone with folder-admin access. See
# INTERN_GUIDE.md Phase 5. This is intentionally left out of this module.

# ---------------------------------------------------------------------------
# Secret Manager
# ---------------------------------------------------------------------------
resource "google_secret_manager_secret" "fs_api_key" {
  project   = var.project_id
  secret_id = local.secret_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "runtime_can_read" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.fs_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

# ---------------------------------------------------------------------------
# Cloud Run Job
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_job" "provisioner" {
  project  = var.project_id
  name     = local.job_name
  location = var.region

  template {
    template {
      service_account = google_service_account.runtime.email
      max_retries      = 1
      timeout          = "300s"

      containers {
        image = var.job_image_ref != "" ? var.job_image_ref : "${var.region}-docker.pkg.dev/${var.project_id}/${local.ar_repo_id}/provisioner-job:placeholder"

        resources {
          limits = {
            cpu    = var.job_cpu
            memory = var.job_memory
          }
        }

        env {
          name  = "FRESHSERVICE_DOMAIN"
          value = var.freshservice_domain
        }
        env {
          name  = "FRESHSERVICE_CATALOG_ITEM_ID"
          value = tostring(var.freshservice_catalog_item_id)
        }
        env {
          name  = "FRESHSERVICE_APPROVER_AGENT_ID"
          value = tostring(var.freshservice_approver_agent_id)
        }
        env {
          name  = "GCP_DEST_FOLDER_ID"
          value = var.gcp_dest_folder_id
        }
        env {
          name  = "GCP_DEST_FOLDER_DISPLAY_NAME"
          value = var.gcp_dest_folder_display_name
        }
        env {
          name  = "MOCK_FRESHSERVICE"
          value = "false"
        }
        env {
          name  = "DRY_RUN"
          value = tostring(var.dry_run)
        }
        env {
          name = "FRESHSERVICE_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.fs_api_key.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [google_project_service.required]
}

# ---------------------------------------------------------------------------
# Cloud Scheduler — triggers the job every N minutes
# ---------------------------------------------------------------------------
resource "google_service_account" "scheduler_invoker" {
  project      = var.project_id
  account_id   = "${var.name_prefix}-sched-inv"
  display_name = "GCP Project Provisioner - scheduler invoker"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_can_run" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.provisioner.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}

resource "google_cloud_scheduler_job" "poll" {
  project  = var.project_id
  region   = var.region
  name     = local.scheduler_id
  schedule = var.poll_schedule

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${local.job_name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_invoker.email
    }
  }

  depends_on = [google_project_service.required]
}
