# One-time bootstrap: creates the GCS bucket that holds Terraform remote
# state for every other stack in this repo. Run once per GCP project, with
# local state (no backend block here — that's the point).

terraform {
  required_version = ">= 1.10"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "GCP project that will host the Terraform state bucket."
}

variable "bucket_name" {
  type        = string
  description = "Globally-unique name for the state bucket."
}

variable "region" {
  type        = string
  default     = "us-west1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "tf_state" {
  name          = var.bucket_name
  project       = var.project_id
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      num_newer_versions = 10
    }
    action {
      type = "Delete"
    }
  }
}

output "bucket_name" {
  value = google_storage_bucket.tf_state.name
}
