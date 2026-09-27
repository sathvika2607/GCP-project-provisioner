# GCP Project Provisioner

A Python job that runs on Google Cloud (Cloud Run Job + Cloud Scheduler,
every 5 minutes) and automates GCP project creation from Freshservice
tickets.

**Flow:** an employee submits a "GCP Project Request" ticket in Freshservice
→ the job validates it → requests approval from a configured approver →
once approved, creates the GCP project (no billing linked) under a fixed
folder and grants the requester `roles/viewer`.

All company-specific values (Freshservice domain, approver, destination
folder, GCP project ID) are placeholders in this repo and are supplied via
environment variables / `terraform.tfvars` — nothing real is hardcoded
anywhere in the code.

## Project layout

```
backend/
  job.py                          Entry point — what Cloud Run Job executes
  app/
    config.py                     All settings read from environment variables
    services/
      freshservice.py             Freshservice REST API v2 client (+ mock mode)
      validator.py                Project-name / label validation rules
      approval_engine.py          Requests approval from the configured approver
      gcp_provisioner.py          Creates the GCP project, grants IAM
      ticket_processor.py         Orchestrates the per-ticket state machine
  Dockerfile
  requirements.txt

infra/
  terraform/
    bootstrap/                    One-time: creates the Terraform state bucket
    environments/dev/             Dev environment (project_id, tfvars, backend)
    modules/provisioner_stack/    All GCP resources: Cloud Run Job, Scheduler,
                                   Artifact Registry, service accounts,
                                   Secret Manager
  cloudbuild/deploy-dev.yaml      Builds & pushes the container image

docs/
  FS_ADMIN_SETUP.md               What the Freshservice admin needs to configure

.env.example                      Local dev config template (placeholders only)
docker-compose.yml                Run the job locally in a container
PLAN.md                           Technical design notes
DEPLOY_DEV.md                     Short deploy runbook
```

## Quick start (local, fully mocked — no credentials needed)

```bash
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd ..
cp .env.example .env      # MOCK_FRESHSERVICE=true and DRY_RUN=true by default
cd backend
python job.py
```

You should see log lines ending in `=== Poll run complete ===` with a mock
ticket getting processed — no network calls, no real credentials required.

## Wiring up real credentials

Nothing in this repo contains real API keys, service account keys, or
company data:

- The Freshservice API key is **never** stored in a file in this repo. Copy
  `.env.example` → `.env` for local dev only (git-ignored), or upload it
  directly to Secret Manager for the deployed job (see Phase 7 in a full
  intern-style walkthrough, or just: `gcloud secrets versions add ...`).
- GCP auth for local runs uses your own `gcloud auth login --update-adc`
  session (Application Default Credentials) — no key file needed.
- `terraform.tfvars` and `backend.hcl` are git-ignored; copy from the
  `.example` files and fill in your own project ID, Freshservice domain,
  and folder ID.

## Hard-coded business rules

Two things are intentionally fixed in code/config rather than read from the
ticket, per the design: the destination GCP folder (`GCP_DEST_FOLDER_ID`)
and the granted IAM role (`roles/viewer`). No billing account is ever linked
to a created project.

See `PLAN.md` for the full design rationale and `DEPLOY_DEV.md` for the
condensed deploy steps.
