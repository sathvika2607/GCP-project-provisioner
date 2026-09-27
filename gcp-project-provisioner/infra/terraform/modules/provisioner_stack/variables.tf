variable "project_id" {
  type        = string
  description = "GCP project the provisioner infrastructure runs in."
}

variable "region" {
  type        = string
  default     = "us-west1"
}

variable "name_prefix" {
  type        = string
  description = "Prefix applied to every resource name, e.g. 'gcp-provisioner-dev'."
}

variable "freshservice_domain" {
  type        = string
  description = "Freshservice domain, e.g. yourcompany-sandbox.freshservice.com"
}

variable "freshservice_catalog_item_id" {
  type        = number
  description = "Service catalog item ID for the GCP Project Request form."
}

variable "freshservice_approver_agent_id" {
  type        = number
  description = "Freshservice agent ID of the approver."
}

variable "gcp_dest_folder_id" {
  type        = string
  description = "GCP folder ID that newly-created projects are placed under."
}

variable "gcp_dest_folder_display_name" {
  type        = string
  description = "Human-readable name of the destination folder, used in ticket notes."
}

variable "poll_schedule" {
  type        = string
  default     = "*/5 * * * *"
  description = "Cron schedule for Cloud Scheduler to trigger the job."
}

variable "dry_run" {
  type        = bool
  default     = true
}

variable "job_image_ref" {
  type        = string
  description = "Fully-qualified container image reference (with tag or digest) to deploy. Leave as a placeholder tag until the first `gcloud builds submit` has run."
  default     = "" # populated after Phase 8 of the intern guide
}

variable "job_cpu" {
  type    = string
  default = "1"
}

variable "job_memory" {
  type    = string
  default = "512Mi"
}
