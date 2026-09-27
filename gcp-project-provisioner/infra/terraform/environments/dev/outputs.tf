output "artifact_registry_repo" {
  value = module.provisioner_stack.artifact_registry_repo
}

output "cloud_run_job_name" {
  value = module.provisioner_stack.cloud_run_job_name
}

output "cloudbuild_sa_email" {
  value = module.provisioner_stack.cloudbuild_sa_email
}

output "fs_api_key_secret_id" {
  value = module.provisioner_stack.fs_api_key_secret_id
}

output "runtime_sa_email" {
  value = module.provisioner_stack.runtime_sa_email
}
