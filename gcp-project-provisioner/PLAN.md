# Technical Plan

## Goal

Automate GCP project creation from a Freshservice self-service form, with a
human approval gate, without granting the automation broad standing
permissions.

## Components

- **Cloud Scheduler** — cron trigger every 5 minutes (configurable via
  `poll_schedule`).
- **Cloud Run Job** — stateless, one-shot execution of `job.py` per trigger.
  No persistent server, no inbound traffic, minimal attack surface.
- **Freshservice REST API v2** — source of truth for tickets and approvals.
  A bot agent account with minimal (non-admin) permissions is used.
- **GCP Resource Manager API** — project creation + IAM binding.
- **Secret Manager** — holds the Freshservice API key; injected into the job
  container as an env var at runtime, never written to disk in the repo.

## State machine (per ticket)

```
No approval yet
  → validate (project name format, department code, required labels)
  → invalid: public note + status=Pending (requester can fix and resubmit)
  → valid:   create Freshservice approval for the configured approver

Approval status = requested
  → no-op, wait for next poll

Approval status = approved
  → create GCP project under the fixed destination folder
  → apply 4 labels (owner, team-alias, application, env)
  → grant roles/viewer to the requester
  → no billing account linked
  → public note with project ID + close ticket

Approval status = rejected
  → public note + close ticket
```

## Idempotency

Before creating a project, `gcp_provisioner.project_already_exists()` checks
whether a project with the computed project_id already exists. If the job
runs twice against the same approved ticket (e.g. a retry), it grants IAM
again but does not attempt to recreate the project.

## Why a job, not a server

The task is periodic and stateless — there's no need for a long-running
service or webhook receiver. A Cloud Run Job triggered by Cloud Scheduler
means no exposed endpoint and a natural retry/timeout boundary per run.

## Permissions model

The runtime service account gets:
- `roles/logging.logWriter` (from this Terraform stack)
- `roles/secretmanager.secretAccessor` on the one Freshservice-key secret
  (from this Terraform stack)
- `roles/resourcemanager.projectCreator` and
  `roles/resourcemanager.projectIamAdmin` **on the destination folder only**
  — granted out-of-band by whoever administers that folder, since folder IAM
  can't be granted from a Terraform stack scoped to a different project.

This keeps the automation's blast radius limited to one folder, with no
billing or org-level permissions.

## Extensibility notes

- Department codes and the project-name regex in `validator.py` are
  placeholders — swap in your organisation's real naming convention.
- `gcp_provisioner.py` assumes a single fixed destination folder; if you
  need per-team folders, route on a label before calling `create_project`.
