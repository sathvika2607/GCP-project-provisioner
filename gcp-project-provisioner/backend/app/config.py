"""
Central configuration.

Every setting comes from an environment variable — nothing is hardcoded here
except the two organisation-wide constants that the business rules require to
be fixed (destination folder + granted role). Secrets (the Freshservice API
key) are never read from a plain env var in production — Terraform wires
Secret Manager to inject them as an env var at container start time, so from
this module's point of view it's still just `os.environ`.
"""

import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int = 0) -> int:
    val = os.environ.get(name)
    if val is None or val == "":
        return default
    return int(val)


@dataclass(frozen=True)
class Settings:
    # --- Freshservice ---
    freshservice_domain: str
    freshservice_api_key: str
    freshservice_catalog_item_id: int
    freshservice_approver_agent_id: int

    # --- Behaviour flags ---
    mock_freshservice: bool
    dry_run: bool

    # --- GCP ---
    gcp_billing_account: str  # intentionally unused for project creation; kept for future use
    gcp_dest_folder_id: str
    gcp_dest_folder_display_name: str

    # --- Fixed business rules (non-negotiable, see INTERN_GUIDE.md) ---
    granted_iam_role: str = "roles/viewer"

    @property
    def freshservice_base_url(self) -> str:
        return f"https://{self.freshservice_domain}/api/v2"


def load_settings() -> Settings:
    return Settings(
        freshservice_domain=os.environ.get("FRESHSERVICE_DOMAIN", ""),
        freshservice_api_key=os.environ.get("FRESHSERVICE_API_KEY", ""),
        freshservice_catalog_item_id=_get_int("FRESHSERVICE_CATALOG_ITEM_ID", 0),
        freshservice_approver_agent_id=_get_int("FRESHSERVICE_APPROVER_AGENT_ID", 0),
        mock_freshservice=_get_bool("MOCK_FRESHSERVICE", True),
        dry_run=_get_bool("DRY_RUN", True),
        gcp_billing_account=os.environ.get("GCP_BILLING_ACCOUNT", ""),
        gcp_dest_folder_id=os.environ.get("GCP_DEST_FOLDER_ID", "000000000000"),
        gcp_dest_folder_display_name=os.environ.get(
            "GCP_DEST_FOLDER_DISPLAY_NAME", "sandbox-projects"
        ),
    )
