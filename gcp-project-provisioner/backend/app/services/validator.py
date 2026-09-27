"""
Validates a ticket's requested project name and labels before anything is
created or an approval is requested.

The project-name convention used here is a placeholder:

    <dept-code>-<team>-<application>-<env>

Adjust VALID_DEPT_CODES and the regex to match your organisation's real
naming convention.
"""

import re
from dataclasses import dataclass, field

# Placeholder department codes — replace with your organisation's real list.
VALID_DEPT_CODES = {"eng", "it", "data", "sec", "sample-team"}

VALID_ENVS = {"dev", "sandbox", "staging", "prod"}

# e.g. "eng-auth-svc-prod"
PROJECT_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){1,4}$")

REQUIRED_LABELS = ("label_owner", "label_team_alias", "label_application", "label_env")


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


def validate_ticket(ticket) -> ValidationResult:
    errors: list[str] = []

    # --- project name format ---
    name = (ticket.project_name or "").strip()
    if not name:
        errors.append("project_name is required")
    elif not PROJECT_NAME_RE.match(name):
        errors.append(
            f"project_name '{name}' is not in the required format "
            "<dept>-<team>-<application>-<env> (lowercase letters, digits, hyphens only)"
        )
    else:
        dept_code = name.split("-")[0]
        if dept_code not in VALID_DEPT_CODES:
            errors.append(
                f"'{dept_code}' is not a recognised department code. "
                f"Valid codes: {', '.join(sorted(VALID_DEPT_CODES))}"
            )

    # --- required labels ---
    for field_name in REQUIRED_LABELS:
        if not getattr(ticket, field_name, None):
            errors.append(f"{field_name} is required")

    # --- env label sanity check ---
    if ticket.label_env and ticket.label_env not in VALID_ENVS:
        errors.append(
            f"label_env '{ticket.label_env}' is not one of: {', '.join(sorted(VALID_ENVS))}"
        )

    return ValidationResult(is_valid=(len(errors) == 0), errors=errors)


def format_validation_note(result: ValidationResult) -> str:
    lines = ["Your GCP project request could not be validated:"]
    for err in result.errors:
        lines.append(f"- {err}")
    lines.append("")
    lines.append("Please update the request and it will be re-checked automatically.")
    return "\n".join(lines)
