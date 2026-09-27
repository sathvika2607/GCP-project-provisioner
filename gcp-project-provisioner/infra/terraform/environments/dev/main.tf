terraform {
  required_version = ">= 1.10"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Values supplied via `-backend-config=backend.hcl` at init time.
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "provisioner_stack" {
  source = "../../modules/provisioner_stack"

  project_id                     = var.project_id
  region                          = var.region
  name_prefix                     = "gcp-provisioner-dev"
  freshservice_domain             = var.freshservice_domain
  freshservice_catalog_item_id    = var.freshservice_catalog_item_id
  freshservice_approver_agent_id  = var.freshservice_approver_agent_id
  gcp_dest_folder_id              = var.gcp_dest_folder_id
  gcp_dest_folder_display_name    = var.gcp_dest_folder_display_name
  poll_schedule                   = var.poll_schedule
  dry_run                         = var.dry_run
  job_image_ref                   = var.job_image_ref
}
