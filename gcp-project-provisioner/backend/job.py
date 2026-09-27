"""
Entry point. This is what Cloud Run Job executes on each trigger from
Cloud Scheduler (every 5 minutes in production).

Run locally with:
    cd backend
    python job.py
"""

import logging
import sys

from app.config import load_settings
from app.services.freshservice import FreshserviceClient
from app.services.ticket_processor import process_ticket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("job")


def run() -> int:
    settings = load_settings()
    logger.info("=== Poll run started ===")

    if settings.mock_freshservice:
        logger.info("MOCK_FRESHSERVICE=true — using canned ticket data, no real API calls")
    if settings.dry_run:
        logger.info("DRY_RUN=true — GCP project creation will be simulated only")

    client = FreshserviceClient(settings)
    exit_code = 0
    try:
        tickets = client.get_open_tickets_for_catalog_item()
        logger.info("Found %d ticket(s) to process", len(tickets))

        for ticket in tickets:
            logger.info(
                "Ticket %s | project='%s' | requester=%s | status=%s",
                ticket.ticket_id,
                ticket.project_name,
                ticket.requester_email,
                ticket.status,
            )
            try:
                process_ticket(client, settings, ticket)
            except Exception:
                logger.exception("Ticket %s: unhandled error while processing", ticket.ticket_id)
                exit_code = 1
    finally:
        client.close()

    logger.info("=== Poll run complete ===")
    return exit_code


if __name__ == "__main__":
    sys.exit(run())
