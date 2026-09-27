output "artifact_registry_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "cloud_run_job_name" {
  value = google_cloud_run_v2_job.provisioner.name
}

output "cloudbuild_sa_email" {
  value = google_service_account.cloudbuild.email
}

output "fs_api_key_secret_id" {
  value = google_secret_manager_secret.fs_api_key.secret_id
}

output "runtime_sa_email" {
  value = google_service_account.runtime.email
}
