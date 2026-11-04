from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.soar.playbooks.containment_lock import (
    ContainmentBusyError,
    ContainmentLock,
)
from app.soar.playbooks.privileged_policy import (
    validate_privileged_request,
)
from app.soar.playbooks.recovery_guard import check_recovery_safety
from app.soar.playbooks.service_recovery import plan_containment


class ServiceBackend(Protocol):
    def recovery_pending(self) -> bool: ...
    def schedule_recovery(self, deadline: str) -> None: ...
    def verify_recovery(self, deadline: str) -> bool: ...
    def stop_demo_service(self) -> None: ...
    def start_demo_service(self) -> None: ...


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    reason: str
    deadline: str | None = None


def contain_demo_service(
        backend: ServiceBackend,
        lock: ContainmentLock,
        *,
        duration_seconds: int = 90,
        now: datetime | None = None,
) -> ExecutionResult:


    policy = validate_privileged_request(
        "contain", "soar-demo.service", duration_seconds
    )

    if not policy.approved:
        return ExecutionResult("rejected", policy.reason)

    try:
        with lock.hold():
            timestamp = now or datetime.now(timezone.utc)

            if backend.recovery_pending():
                return ExecutionResult(
                    "rejected", "Recovery already pending."
                )

            plan = plan_containment(
                "soar-demo.service",
                duration_seconds,
                authorized=True,
                now=timestamp,
            )

            safety = check_recovery_safety(
                plan,
                existing_recovery=False,
                now=timestamp,
            )

            if not safety.approved:
                return ExecutionResult("rejected", safety.reason)


            backend.schedule_recovery(plan.deadline)

            if not backend.verify_recovery(plan.deadline):
                return ExecutionResult(
                    "failed",
                    "Recovery scheduling could not be verified; "
                    "service was not stopped.",
                    plan.deadline,
                )

            try:
                backend.stop_demo_service()
            except Exception:

                try:
                    backend.start_demo_service()
                except Exception:
                    pass

                return ExecutionResult(
                    "failed",
                    "Containment failed; immediate restoration "
                    "was attempted.",
                    plan.deadline,
                )

            return ExecutionResult(
                "contained",
                "Demo service stopped with recovery scheduled.",
                plan.deadline,
            )

    except ContainmentBusyError:
        return ExecutionResult(
            "rejected", "Containment operation already locked."
        )
    except Exception:
        return ExecutionResult(
            "failed",
            "Backend operation failed; containment was not requested.",
        )
