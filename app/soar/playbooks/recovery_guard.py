
"""Safety checks before scheduling live service recovery.

No operating-system commands are executed here.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.soar.playbooks.service_recovery import (
    DEMO_SERVICE,
    RecoveryPlan,
)


@dataclass(frozen=True)
class RecoveryGuardResult:
    approved: bool
    reason: str


def check_recovery_safety(
        plan: RecoveryPlan,
        *,
        existing_recovery: bool,
        now: datetime | None = None,
) -> RecoveryGuardResult:

    if not plan.approved or plan.service != DEMO_SERVICE:
        return RecoveryGuardResult(False, "Unapproved service or plan.")

    if existing_recovery:
        return RecoveryGuardResult(
            False,
            "A recovery operation already exists.",
        )

    try:
        deadline = datetime.fromisoformat(plan.deadline)
    except (TypeError, ValueError):
        return RecoveryGuardResult(False, "Invalid recovery deadline.")

    if deadline.tzinfo is None:
        return RecoveryGuardResult(
            False,
            "Recovery deadline must contain a timezone.",
        )

    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        return RecoveryGuardResult(
            False,
            "Current time must contain a timezone.",
        )

    remaining = (
            deadline.astimezone(timezone.utc)
            - current_time.astimezone(timezone.utc)
    ).total_seconds()

    if not 60 <= remaining <= 300:
        return RecoveryGuardResult(
            False,
            "Recovery deadline must be 60–300 seconds in the future.",
        )

    return RecoveryGuardResult(
        True,
        "Recovery scheduling may proceed.",
    )
