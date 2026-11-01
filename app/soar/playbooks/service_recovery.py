
"""Plan safe, time-limited containment of the disposable test service.

This module does NOT execute systemctl commands.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


DEMO_SERVICE = "soar-demo.service"
MIN_DURATION = 60
MAX_DURATION = 300


@dataclass(frozen=True)
class RecoveryPlan:
    approved: bool
    service: str
    deadline: str | None
    reason: str


def plan_containment(
        service: str,
        duration_seconds: int = 90,
        *,
        authorized: bool = False,
        pending_recovery: bool = False,
        now: datetime | None = None,
) -> RecoveryPlan:
    """Validate a request and calculate its recovery deadline."""

    if service != DEMO_SERVICE:
        return RecoveryPlan(
            False, service, None,
            "Only the disposable demo service is supported.",
        )

    if not authorized:
        return RecoveryPlan(
            False, service, None,
            "Live containment has not been authorized.",
        )

    if pending_recovery:
        return RecoveryPlan(
            False, service, None,
            "A recovery operation is already pending.",
        )

    if (
            type(duration_seconds) is not int
            or not MIN_DURATION <= duration_seconds <= MAX_DURATION
    ):
        return RecoveryPlan(
            False, service, None,
            "Duration must be between 60 and 300 seconds.",
        )

    timestamp = now or datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        return RecoveryPlan(
            False, service, None,
            "A timezone-aware timestamp is required.",
        )

    timestamp = timestamp.astimezone(timezone.utc)
    deadline = timestamp + timedelta(seconds=duration_seconds)

    return RecoveryPlan(
        True,
        service,
        deadline.isoformat(),
        "Request validated; recovery must be scheduled before stopping.",
    )
