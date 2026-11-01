
"""Fixed policy for the future privileged SOAR helper.

This module cannot execute commands.
"""

from dataclasses import dataclass

from app.soar.playbooks.service_recovery import (
    DEMO_SERVICE,
    MAX_DURATION,
    MIN_DURATION,
)


@dataclass(frozen=True)
class PrivilegedRequest:
    approved: bool
    operation: str
    service: str
    duration_seconds: int
    reason: str


def validate_privileged_request(
        operation: str,
        service: str,
        duration_seconds: int,
) -> PrivilegedRequest:
    """Apply an independent, fixed containment policy."""

    reason = ""

    if operation != "contain":
        reason = "Unsupported privileged operation."
    elif service != DEMO_SERVICE:
        reason = "Only the disposable demo service is permitted."
    elif type(duration_seconds) is not int:
        reason = "Duration must be an integer."
    elif not MIN_DURATION <= duration_seconds <= MAX_DURATION:
        reason = "Duration is outside the permitted range."

    return PrivilegedRequest(
        approved=not bool(reason),
        operation=operation,
        service=service,
        duration_seconds=duration_seconds,
        reason=reason or "Request satisfies the fixed helper policy.",
    )
