# Deploy Runbook (dev)

Condensed steps — see `README.md` for the fuller local quick-start.

1. **Bootstrap state bucket** (once):
   ```bash
   terraform -chdir=infra/terraform/bootstrap init
   terraform -chdir=infra/terraform/bootstrap apply \
     -var="project_id=your-project-id" \
     -var="bucket_name=your-project-id-tfstate"
   ```

2. **Configure dev environment**:
   ```bash
   cp infra/terraform/environments/dev/backend.hcl.example infra/terraform/environments/dev/backend.hcl
   cp infra/terraform/environments/dev/terraform.tfvars.example infra/terraform/environments/dev/terraform.tfvars
   # edit both files with your real project_id, FS domain, folder ID, etc.
   ```

3. **Init & apply**:
   ```bash
   terraform -chdir=infra/terraform/environments/dev init \
     -backend-config=infra/terraform/environments/dev/backend.hcl
   terraform -chdir=infra/terraform/environments/dev apply
   ```

4. **Grant folder IAM** (done by whoever administers the destination
   folder, using the `runtime_sa_email` from step 3's output):
   ```bash
   gcloud resource-manager folders add-iam-policy-binding <FOLDER_ID> \
     --member="serviceAccount:<runtime-sa-email>" \
     --role="roles/resourcemanager.projectCreator"
   gcloud resource-manager folders add-iam-policy-binding <FOLDER_ID> \
     --member="serviceAccount:<runtime-sa-email>" \
     --role="roles/resourcemanager.projectIamAdmin"
   ```

5. **Upload the Freshservice API key** to the secret Terraform created
   (`fs_api_key_secret_id` from the output):
   ```bash
   echo -n "YOUR-BOT-AGENT-API-KEY" | gcloud secrets versions add \
     <SECRET_ID> --data-file=- --project=your-project-id
   ```

6. **Build & push the image**:
   ```bash
   gcloud builds submit \
     --project=your-project-id \
     --region=us-west1 \
     --service-account="projects/your-project-id/serviceAccounts/<cloudbuild_sa_email>" \
     --config=infra/cloudbuild/deploy-dev.yaml \
     --substitutions="_REGION=us-west1,_AR_REPO=gcp-provisioner,_IMAGE=provisioner-job,_IMAGE_TAG=dev-$(date -u +%Y%m%d-%H%M)" \
     .
   ```
   Pin the resulting digest into `job_image_ref` in `terraform.tfvars`, then
   `terraform apply` again.

7. **Test run**:
   ```bash
   gcloud run jobs execute <cloud_run_job_name> --region=us-west1 --project=your-project-id --wait
   ```

8. Once all validation/approval/provisioning scenarios pass with
   `dry_run = true`, set `dry_run = false` and re-apply.
