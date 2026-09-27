"""
Orchestrates the per-ticket state machine described in INTERN_GUIDE.md:

    no approval yet        -> validate, then either flag as Pending or
                               request an approval
    approval "requested"   -> nothing to do yet
    approval "approved"    -> create the GCP project, grant viewer, close ticket
    approval "rejected"    -> add a rejection note, close ticket
"""

import logging

from app.config import Settings
from app.services import approval_engine, gcp_provisioner, validator
from app.services.freshservice import (
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    APPROVAL_REQUESTED,
    STATUS_PENDING,
    FreshserviceClient,
    TicketFields,
)

logger = logging.getLogger(__name__)


def process_ticket(client: FreshserviceClient, settings: Settings, ticket: TicketFields) -> None:
    approval_status = client.get_approval_status(ticket.ticket_id)

    if approval_status is None:
        _handle_no_approval(client, settings, ticket)
    elif approval_status == APPROVAL_REQUESTED:
        logger.info("Ticket %s: approval still pending — nothing to do", ticket.ticket_id)
    elif approval_status == APPROVAL_APPROVED:
        _handle_approved(client, settings, ticket)
    elif approval_status == APPROVAL_REJECTED:
        _handle_rejected(client, ticket)
    else:
        logger.warning("Ticket %s: unrecognised approval status '%s'", ticket.ticket_id, approval_status)


def _handle_no_approval(client: FreshserviceClient, settings: Settings, ticket: TicketFields) -> None:
    result = validator.validate_ticket(ticket)

    if not result.is_valid:
        note = validator.format_validation_note(result)
        client.add_public_note(ticket.ticket_id, note)
        client.set_status(ticket.ticket_id, STATUS_PENDING)
        logger.info("Ticket %s failed validation — set to Pending", ticket.ticket_id)
        return

    approval_engine.request_approval(client, settings, ticket.ticket_id)


def _handle_approved(client: FreshserviceClient, settings: Settings, ticket: TicketFields) -> None:
    try:
        project_id = gcp_provisioner.create_project(settings, ticket, dry_run=settings.dry_run)
    except gcp_provisioner.ProvisioningError as e:
        client.add_public_note(
            ticket.ticket_id,
            f"Project creation failed and needs manual follow-up: {e}",
        )
        logger.error("Ticket %s: provisioning failed: %s", ticket.ticket_id, e)
        return

    if settings.dry_run:
        note = f"[DRY RUN] Would have created project '{project_id}'. No changes were made."
    else:
        note = (
            f"Your GCP project has been created.\n\n"
            f"Project ID: {project_id}\n"
            f"Folder: {settings.gcp_dest_folder_display_name}\n"
            f"Role granted: {settings.granted_iam_role} (to {ticket.requester_email})\n"
            f"Billing account: none linked."
        )
    client.add_public_note(ticket.ticket_id, note)
    client.close_ticket(ticket.ticket_id)


def _handle_rejected(client: FreshserviceClient, ticket: TicketFields) -> None:
    client.add_public_note(
        ticket.ticket_id,
        "Your GCP project request was rejected by the approver. "
        "Reach out to your approver if you have questions.",
    )
    client.close_ticket(ticket.ticket_id)
