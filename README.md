# GCP Project Provisioner 🚀

An automated GCP project provisioning tool that processes **Freshservice GCP project requests**, validates the request, obtains approval, and provisions the Google Cloud project automatically.

The application runs as a **Google Cloud Run Job**, triggered every **5 minutes by Cloud Scheduler**. It integrates with the **Freshservice REST API** for ticket management and the **GCP Resource Manager API** for project creation and IAM configuration.

---

## 🏗️ Architecture

```text
                  Every 5 Minutes
                       │
                       ▼
              ┌─────────────────┐
              │ Cloud Scheduler  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Cloud Run Job   │
              │     job.py       │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
     ┌───────────────┐   ┌────────────────────┐
     │ Freshservice  │   │ GCP Resource       │
     │ REST API      │   │ Manager API        │
     └───────────────┘   └────────────────────┘
             │                   │
             ▼                   ▼
       Tickets & Approval    GCP Projects
```

The provisioner:

1. Reads GCP project requests from Freshservice.
2. Validates the project name and required labels.
3. Creates an approval request.
4. Waits for approval or rejection.
5. Creates the GCP project after approval.
6. Grants the requester `roles/viewer`.
7. Updates and closes the Freshservice ticket.

---

## ✨ Features

* Automated GCP project provisioning
* Freshservice ticket integration
* Project name validation
* Required label validation
* Approval and rejection workflow
* Automated IAM configuration
* Cloud Run Job execution
* Cloud Scheduler integration
* Terraform-based infrastructure
* Docker containerization
* Cloud Build deployment
* Secret Manager integration
* Dry-run mode for safe testing
* Mock Freshservice mode for local development
* Idempotent project provisioning

---

## 🔐 Provisioning Rules

The following rules are enforced by the provisioner:

* All projects are created under the `it-systems-interns` folder.
* Folder ID: `901333113307`
* The requester receives only `roles/viewer`.
* No billing account is linked to automatically created projects.
* Freshservice authentication uses a bot account with minimal permissions.

---

## 📁 Project Structure

```text
gcp-project-provisioner/
│
├── backend/
│   ├── job.py
│   ├── app/
│   │   ├── config.py
│   │   └── services/
│   │       ├── freshservice.py
│   │       ├── validator.py
│   │       ├── approval_engine.py
│   │       ├── gcp_provisioner.py
│   │       └── ticket_processor.py
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── infra/
│   ├── terraform/
│   │   ├── bootstrap/
│   │   ├── environments/
│   │   │   └── dev/
│   │   └── modules/
│   │       └── provisioner_stack/
│   │
│   └── cloudbuild/
│       └── deploy-dev.yaml
│
├── docs/
│   └── FS_ADMIN_SETUP.md
│
├── INTERN_GUIDE.md
├── PLAN.md
├── DEPLOY_DEV.md
├── docker-compose.yml
└── .env.example
```

The backend separates Freshservice integration, validation, approval handling, GCP provisioning, and ticket orchestration into dedicated services.

---

## 🛠️ Technology Stack

| Technology               | Purpose                           |
| ------------------------ | --------------------------------- |
| Python 3.12              | Application development           |
| Google Cloud Run Jobs    | Run the provisioning job          |
| Cloud Scheduler          | Trigger the job every 5 minutes   |
| GCP Resource Manager API | Create GCP projects               |
| Freshservice REST API    | Ticket and approval management    |
| Terraform                | Infrastructure as Code            |
| Docker                   | Application containerization      |
| Cloud Build              | Build and deploy container images |
| Artifact Registry        | Store Docker images               |
| Secret Manager           | Secure API key storage            |

---

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd gcp-project-provisioner
```

### 2. Create a virtual environment

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Example:

```env
FRESHSERVICE_DOMAIN=yourcompany-sandbox.freshservice.com
FRESHSERVICE_API_KEY=your-api-key
FRESHSERVICE_CATALOG_ITEM_ID=0
FRESHSERVICE_APPROVER_AGENT_ID=0

MOCK_FRESHSERVICE=true
DRY_RUN=true
```

The API key should **never be committed to GitHub**. In the deployed environment, it is stored in Google Cloud Secret Manager.

---

## 🧪 Run Locally

For local testing, enable mock Freshservice data and GCP dry-run mode:

```env
MOCK_FRESHSERVICE=true
DRY_RUN=true
```

Then:

```bash
cd backend
python job.py
```

A successful run should show messages similar to:

```text
=== Poll run started ===
Found 1 ticket(s) to process
Ticket 99999 | project='it-sys-auth-prod'
Ticket 99999 passed validation
Creating Freshservice approval
Approval created
=== Poll run complete ===
```

The mock and dry-run modes allow the workflow to be tested without making real Freshservice or GCP changes.

---

## 🔄 Workflow

```text
Freshservice Request
        │
        ▼
Validate Request
        │
   ┌────┴─────┐
   │          │
Invalid      Valid
   │          │
   ▼          ▼
Add Note   Create Approval
Pending        │
               ▼
          Approval Decision
          ┌────┴────┐
          │         │
       Approved   Rejected
          │         │
          ▼         ▼
     Create GCP   Add Rejection
      Project        Note
          │           │
          ▼           ▼
     Grant Viewer   Close Ticket
          │
          ▼
      Close Ticket
```

---

## ☁️ Infrastructure Deployment

Terraform provisions the required GCP infrastructure, including:

* Artifact Registry
* Cloud Run Job
* Cloud Scheduler
* Service Accounts
* IAM permissions
* Secret Manager resources

The Terraform configuration is organized into bootstrap, development environment, and reusable infrastructure modules.

Initialize Terraform:

```bash
terraform -chdir=infra/terraform/environments/dev init
```

Review the infrastructure:

```bash
terraform -chdir=infra/terraform/environments/dev plan
```

Apply:

```bash
terraform -chdir=infra/terraform/environments/dev apply
```

---

## 🐳 Docker

The application is packaged as a Docker container and executed using Cloud Run Jobs.

Build locally:

```bash
docker build -t gcp-project-provisioner ./backend
```

Run:

```bash
docker run --env-file .env gcp-project-provisioner
```

---

## 🚀 Deployment

The project uses **Cloud Build** to build and push the Docker image to Artifact Registry.

Example:

```bash
gcloud builds submit \
  --project="${PROJECT}" \
  --region=us-west1 \
  --config=infra/cloudbuild/deploy-dev.yaml \
  .
```

After deployment, the Cloud Run Job can be triggered manually:

```bash
gcloud run jobs execute "${JOB_NAME}" \
  --region=us-west1 \
  --project="${PROJECT}" \
  --wait
```

Cloud Scheduler then triggers the job automatically every five minutes.

---

## 🔒 Security

Sensitive credentials are not stored in source code.

The Freshservice API key is stored in **Google Cloud Secret Manager** and accessed by the runtime environment.

Recommended practices:

* Never commit `.env`
* Never commit API keys
* Never commit service-account private keys
* Use Secret Manager for credentials
* Use least-privilege IAM permissions
* Keep `DRY_RUN=true` during testing

---

## 🧪 Testing

The project supports several validation scenarios:

### Invalid project name

```text
my project
```

Expected:

```text
Validation failed
→ Add public note
→ Set ticket to Pending
```

### Invalid department code

```text
xx-sys-auth-prod
```

Expected:

```text
Validation failed
→ Display valid department codes
```

### Missing label

```text
label_team_alias = empty
```

Expected:

```text
Validation failed
→ Add note specifying missing label
```

### Valid request

```text
project_name = it-sys-auth-sandbox
label_owner = user@arista.com
label_team_alias = it-sys
label_application = auth
label_env = sandbox
```

Expected:

```text
Validation successful
→ Freshservice approval created
```

---

## 📊 Acceptance Criteria

The system is considered ready when:

* [ ] Local mock execution succeeds
* [ ] Invalid project names are rejected
* [ ] Invalid department codes are rejected
* [ ] Missing labels are detected
* [ ] Valid requests create approvals
* [ ] Approved requests create GCP projects
* [ ] Rejected requests close correctly
* [ ] Projects are created under the required folder
* [ ] Required labels are applied
* [ ] `roles/viewer` is granted
* [ ] No billing account is linked
* [ ] Duplicate project requests are handled idempotently
* [ ] Freshservice tickets are closed correctly
* [ ] Cloud Scheduler runs every 5 minutes
* [ ] Terraform deployment completes successfully

---

## 📝 Environment Variables

| Variable                         | Description                        |
| -------------------------------- | ---------------------------------- |
| `FRESHSERVICE_DOMAIN`            | Freshservice sandbox/domain        |
| `FRESHSERVICE_API_KEY`           | Freshservice bot API key           |
| `FRESHSERVICE_CATALOG_ITEM_ID`   | GCP request catalog item ID        |
| `FRESHSERVICE_APPROVER_AGENT_ID` | Approver agent ID                  |
| `MOCK_FRESHSERVICE`              | Enables mock Freshservice mode     |
| `DRY_RUN`                        | Prevents real GCP project creation |

---

## 👩‍💻 Project Purpose

This project demonstrates how cloud infrastructure provisioning can be automated through an IT service-management workflow.

Instead of manually creating GCP projects for every request, the system connects **Freshservice → approval workflow → GCP APIs**, reducing manual provisioning steps and providing a controlled approval process.

---

## 📌 Important

This repository is intended for authorized development and deployment within the organization's GCP and Freshservice environments.

Do not commit:

```text
.env
API keys
Service account private keys
Credentials
Secrets
Terraform state files
```

---

## 📄 Documentation

Additional project documentation:

* `INTERN_GUIDE.md` — Complete setup and deployment guide
* `PLAN.md` — Technical implementation plan
* `DEPLOY_DEV.md` — Development deployment instructions
* `docs/FS_ADMIN_SETUP.md` — Freshservice administrator setup

---

## 👤 Author

**Sathvika Mahamkali**

GCP Project Provisioner — Internship Project
