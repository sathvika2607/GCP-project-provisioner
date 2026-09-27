"""
Wraps the "create an approval for the configured approver" step so
ticket_processor.py doesn't need to know Freshservice specifics.
"""

import logging

from app.config import Settings
from app.services.freshservice import FreshserviceClient

logger = logging.getLogger(__name__)


def request_approval(client: FreshserviceClient, settings: Settings, ticket_id: int) -> None:
    approver_id = settings.freshservice_approver_agent_id
    logger.info("Ticket %s passed validation — creating FS approval for %s", ticket_id, approver_id)
    client.create_approval(ticket_id, approver_id)
