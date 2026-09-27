# Freshservice Admin Setup

This is for whoever administers your Freshservice instance. It describes the
service catalog item ("GCP Project Request" form) the provisioner job reads
from.

## 1. Create the Service Catalog Item

Name: `GCP Project Request`

Add these custom fields (field names matter — the job reads them by exact
key name):

| Field label      | Field key (custom_fields key) | Type        | Required |
|-------------------|-------------------------------|-------------|----------|
| Project Name       | `project_name`                | Text        | Yes      |
| Owner Email         | `label_owner`                 | Text        | Yes      |
| Team Alias           | `label_team_alias`            | Text        | Yes      |
| Application            | `label_application`           | Text        | Yes      |
| Environment              | `label_env`                   | Dropdown (dev/sandbox/staging/prod) | Yes |

If your Freshservice instance names these fields differently (e.g. it
auto-prefixes with `cf_`), update
`backend/app/services/freshservice.py::extract_ticket_fields()` to match —
see Phase 3 of `INTERN_GUIDE.md`.

## 2. Create the bot agent account

Create a Freshservice agent with the **minimum permissions needed**:
read/update tickets, create approvals, add notes. Do not grant admin.
Generate an API key for this agent — that key is what goes into Secret
Manager (never into a file that gets committed).

## 3. Note the IDs the job needs

- **Catalog item ID** — found via `GET /api/v2/service_catalog/items`
- **Approver agent ID** — found via `GET /api/v2/agents?email=<approver-email>`

Both go into `terraform.tfvars` (see `infra/terraform/environments/dev/terraform.tfvars.example`).

## 4. Approval workflow

No separate workflow automation is required in Freshservice itself — the job
creates the approval via API (`POST /api/v2/tickets/{id}/approvals`) and
polls its status on each run.
