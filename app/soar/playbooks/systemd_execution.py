
"""Build a restricted systemd execution plan.

This module never executes operating-system commands.
"""

from dataclasses import dataclass
from datetime import datetime
from ipaddress import ip_address

from app.soar.playbooks.service_recovery import (
    DEMO_SERVICE,
    RecoveryPlan,
)


RESTORE_SERVICE = "soar-demo-restore.service"
RESTORE_TIMER = "soar-demo-restore.timer"


@dataclass(frozen=True)
class SystemdExecutionPlan:
    approved: bool
    recovery_deadline: str | None
    recovery_command: tuple[str, ...]
    containment_command: tuple[str, ...]
    reason: str


def build_execution_plan(plan: RecoveryPlan) -> SystemdExecutionPlan:
    """Translate a validated recovery plan into restricted commands."""

    rejected = SystemdExecutionPlan(
        approved=False,
        recovery_deadline=None,
        recovery_command=(),
        containment_command=(),
        reason="Execution plan was rejected.",
    )

    if not plan.approved or plan.service != DEMO_SERVICE:
        return rejected

    if not plan.deadline:
        return rejected

    try:
        deadline = datetime.fromisoformat(plan.deadline)
    except (ValueError, TypeError):
        return rejected

    if deadline.tzinfo is None:
        return rejected

    # Generate a normalized timestamp for a calendar timer.
    from datetime import timezone

    deadline = deadline.astimezone(timezone.utc)
    calendar_time = deadline.strftime("%Y-%m-%d %H:%M:%S UTC")

    return SystemdExecutionPlan(
        approved=True,
        recovery_deadline=calendar_time,
        recovery_command=(
            "/usr/bin/systemctl",
            "start",
            RESTORE_TIMER,
        ),
        containment_command=(
            "/usr/bin/systemctl",
            "stop",
            DEMO_SERVICE,
        ),
        reason="Commands prepared; no actions executed.",
    )
