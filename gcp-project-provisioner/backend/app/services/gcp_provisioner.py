"""
Creates the GCP project and grants IAM, via the Resource Manager API.

Uses Application Default Credentials — locally that's whatever
`gcloud auth login --update-adc` set up; in Cloud Run Job it's the runtime
service account attached by Terraform.

Destination folder and granted role are read from Settings (not from the
ticket) — see the "Hard Rules" section of INTERN_GUIDE.md: these are meant
to be fixed, not attacker- or requester-controlled.
"""

import logging
import re
import time

from google.api_core.exceptions import AlreadyExists, GoogleAPIError
from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2, policy_pb2

from app.config import Settings

logger = logging.getLogger(__name__)


class ProvisioningError(Exception):
    pass


def _sanitize_project_id(name: str) -> str:
    """GCP project IDs must be 6-30 chars, lowercase letters/digits/hyphens,
    start with a letter. Our ticket names already roughly fit; this just
    guards the edges."""
    pid = re.sub(r"[^a-z0-9-]", "-", name.lower())
    if not pid[0].isalpha():
        pid = "p-" + pid
    return pid[:30].rstrip("-")


def project_already_exists(settings: Settings, project_id: str) -> bool:
    """Idempotency check: don't create a second project for the same name."""
    client = resourcemanager_v3.ProjectsClient()
    try:
        client.get_project(name=f"projects/{project_id}")
        return True
    except GoogleAPIError:
        return False


def create_project(settings: Settings, ticket, dry_run: bool) -> str:
    """
    Creates a GCP project under the configured folder, with the 4 labels
    from the ticket, no billing account linked. Returns the project_id.
    """
    project_id = _sanitize_project_id(ticket.project_name)
    labels = {
        "owner": _sanitize_label_value(ticket.label_owner),
        "team-alias": _sanitize_label_value(ticket.label_team_alias),
        "application": _sanitize_label_value(ticket.label_application),
        "env": _sanitize_label_value(ticket.label_env),
    }

    if dry_run:
        logger.info(
            "[DRY RUN] Would create project '%s' under folder %s with labels %s "
            "and grant %s to %s",
            project_id,
            settings.gcp_dest_folder_id,
            labels,
            settings.granted_iam_role,
            ticket.requester_email,
        )
        return project_id

    if project_already_exists(settings, project_id):
        logger.info("Project '%s' already exists — skipping creation (idempotent)", project_id)
        _grant_viewer_role(settings, project_id, ticket.requester_email)
        return project_id

    client = resourcemanager_v3.ProjectsClient()
    project = resourcemanager_v3.Project(
        project_id=project_id,
        display_name=project_id,
        parent=f"folders/{settings.gcp_dest_folder_id}",
        labels=labels,
    )

    try:
        operation = client.create_project(project=project)
        result = operation.result(timeout=120)
        logger.info("Created GCP project '%s'", result.project_id)
    except AlreadyExists:
        logger.info("Project '%s' already exists — continuing", project_id)
    except GoogleAPIError as e:
        raise ProvisioningError(f"Failed to create project '{project_id}': {e}") from e

    _wait_for_project_active(client, project_id)
    _grant_viewer_role(settings, project_id, ticket.requester_email)
    return project_id


def _wait_for_project_active(client, project_id: str, attempts: int = 10, delay_seconds: int = 3) -> None:
    for _ in range(attempts):
        proj = client.get_project(name=f"projects/{project_id}")
        if proj.state == resourcemanager_v3.Project.State.ACTIVE:
            return
        time.sleep(delay_seconds)
    logger.warning("Project '%s' did not report ACTIVE state within timeout", project_id)


def _grant_viewer_role(settings: Settings, project_id: str, requester_email: str) -> None:
    client = resourcemanager_v3.ProjectsClient()
    resource = f"projects/{project_id}"

    policy = client.get_iam_policy(
        request=iam_policy_pb2.GetIamPolicyRequest(resource=resource)
    )

    member = f"user:{requester_email}"
    role = settings.granted_iam_role

    binding_found = False
    for binding in policy.bindings:
        if binding.role == role:
            if member not in binding.members:
                binding.members.append(member)
            binding_found = True
            break
    if not binding_found:
        policy.bindings.append(policy_pb2.Binding(role=role, members=[member]))

    client.set_iam_policy(
        request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy)
    )
    logger.info("Granted %s to %s on project '%s'", role, requester_email, project_id)


def _sanitize_label_value(value: str) -> str:
    """GCP label values: lowercase letters, digits, hyphens/underscores, <=63 chars."""
    if not value:
        return "unspecified"
    v = re.sub(r"[^a-z0-9_-]", "-", value.lower())
    return v[:63]
