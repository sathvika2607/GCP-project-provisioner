"""
Thin client around the Freshservice REST API v2.

Only the handful of endpoints this job needs are wrapped here: listing
tickets for our catalog item, reading/creating approvals, adding notes, and
closing tickets. When MOCK_FRESHSERVICE=true, every call is swapped for
canned data so the job can be exercised with no network access and no real
API key.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

# Freshservice ticket status codes
STATUS_OPEN = 2
STATUS_PENDING = 3
STATUS_RESOLVED = 4
STATUS_CLOSED = 5

# Freshservice approval status strings
APPROVAL_REQUESTED = "requested"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"


@dataclass
class TicketFields:
    ticket_id: int
    status: int
    requester_email: str
    project_name: Optional[str]
    label_owner: Optional[str]
    label_team_alias: Optional[str]
    label_application: Optional[str]
    label_env: Optional[str]
    approval_status: Optional[str] = None
    raw: dict = field(default_factory=dict)


class FreshserviceClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = httpx.Client(
            auth=(settings.freshservice_api_key, "X"),
            base_url=settings.freshservice_base_url,
            timeout=30.0,
        )

    # ------------------------------------------------------------------
    # Ticket listing
    # ------------------------------------------------------------------
    def get_open_tickets_for_catalog_item(self) -> list[TicketFields]:
        if self.settings.mock_freshservice:
            return self._mock_tickets()

        resp = self._client.get(
            "/tickets",
            params={"filter": "new_and_my_open", "include": "requested_items"},
        )
        resp.raise_for_status()
        tickets_raw = resp.json().get("tickets", [])

        result = []
        for t in tickets_raw:
            if t.get("status") not in (STATUS_OPEN, STATUS_PENDING):
                continue
            if not self._matches_catalog_item(t):
                continue
            result.append(self.extract_ticket_fields(t))
        return result

    def _matches_catalog_item(self, ticket_raw: dict) -> bool:
        items = ticket_raw.get("requested_items") or []
        for item in items:
            if item.get("service_item_id") == self.settings.freshservice_catalog_item_id:
                return True
        return False

    def extract_ticket_fields(self, ticket_raw: dict) -> TicketFields:
        """
        Maps Freshservice's custom_fields keys to our internal field names.

        NOTE: These key names (`project_name`, `label_owner`, ...) must match
        whatever the Freshservice admin actually named the fields on the
        "GCP Project Request" form. If they don't match, update the
        `cf.get(...)` calls below — see docs/FS_ADMIN_SETUP.md.
        """
        cf = ticket_raw.get("custom_fields", {}) or {}
        return TicketFields(
            ticket_id=ticket_raw["id"],
            status=ticket_raw.get("status", STATUS_OPEN),
            requester_email=ticket_raw.get("requester", {}).get("email", ""),
            project_name=cf.get("project_name"),
            label_owner=cf.get("label_owner"),
            label_team_alias=cf.get("label_team_alias"),
            label_application=cf.get("label_application"),
            label_env=cf.get("label_env"),
            raw=ticket_raw,
        )

    # ------------------------------------------------------------------
    # Approvals
    # ------------------------------------------------------------------
    def get_approval_status(self, ticket_id: int) -> Optional[str]:
        if self.settings.mock_freshservice:
            return None  # mock tickets never already have an approval

        resp = self._client.get(f"/tickets/{ticket_id}/approvals")
        resp.raise_for_status()
        approvals = resp.json().get("approvals", [])
        if not approvals:
            return None
        # Most recent approval wins
        return approvals[-1].get("approval_status_name", "").lower()

    def create_approval(self, ticket_id: int, approver_agent_id: int) -> None:
        if self.settings.mock_freshservice:
            logger.info("[MOCK] Created approval on ticket %s for agent %s", ticket_id, approver_agent_id)
            return

        payload = {"approver_id": approver_agent_id, "approval_type": 1}
        resp = self._client.post(f"/tickets/{ticket_id}/approvals", json=payload)
        resp.raise_for_status()
        logger.info("Approval created on ticket %s for agent %s", ticket_id, approver_agent_id)

    # ------------------------------------------------------------------
    # Notes / closing
    # ------------------------------------------------------------------
    def add_public_note(self, ticket_id: int, body: str) -> None:
        if self.settings.mock_freshservice:
            logger.info("[MOCK] Note on ticket %s: %s", ticket_id, body)
            return

        payload = {"body": body, "private": False}
        resp = self._client.post(f"/tickets/{ticket_id}/notes", json=payload)
        resp.raise_for_status()

    def set_status(self, ticket_id: int, status: int) -> None:
        if self.settings.mock_freshservice:
            logger.info("[MOCK] Set ticket %s status to %s", ticket_id, status)
            return

        resp = self._client.put(f"/tickets/{ticket_id}", json={"status": status})
        resp.raise_for_status()

    def close_ticket(self, ticket_id: int) -> None:
        self.set_status(ticket_id, STATUS_CLOSED)

    # ------------------------------------------------------------------
    # Mock data (used when MOCK_FRESHSERVICE=true)
    # ------------------------------------------------------------------
    def _mock_tickets(self) -> list[TicketFields]:
        return [
            TicketFields(
                ticket_id=99999,
                status=STATUS_OPEN,
                requester_email="requester@example.com",
                project_name="sample-team-auth-prod",
                label_owner="requester@example.com",
                label_team_alias="sample-team",
                label_application="auth",
                label_env="prod",
            )
        ]

    def close(self) -> None:
        self._client.close()
