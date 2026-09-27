variable "project_id" {
  type        = string
  description = "GCP project hosting the provisioner infra (the tool's own project, NOT the folder it creates projects into)."
}

variable "region" {
  type    = string
  default = "us-west1"
}

variable "freshservice_domain" {
  type        = string
  description = "e.g. yourcompany-sandbox.freshservice.com"
}

variable "freshservice_catalog_item_id" {
  type = number
}

variable "freshservice_approver_agent_id" {
  type = number
}

variable "gcp_dest_folder_id" {
  type        = string
  description = "Folder ID that newly-created GCP projects are placed under."
}

variable "gcp_dest_folder_display_name" {
  type    = string
  default = "sandbox-projects"
}

variable "poll_schedule" {
  type    = string
  default = "*/5 * * * *"
}

variable "dry_run" {
  type    = bool
  default = true
}

variable "job_image_ref" {
  type        = string
  default     = ""
  description = "Populated after the first image build (Phase 8 of the intern guide)."
}
