
"""Restricted systemd backend for disposable SOAR service testing.

Only read-only systemd inspection is implemented.
No containment or timer modification is permitted.
"""

import subprocess
from typing import Callable
from datetime import datetime, timezone


DEMO_SERVICE = "soar-demo.service"
RESTORE_TIMER = "soar-demo-restore.timer"


class SystemdBackend:
    def __init__(
            self,
            runner: Callable = subprocess.run,
    ):
        self.runner = runner

    def _check_unit(self, unit: str) -> str:
        if unit not in (DEMO_SERVICE, RESTORE_TIMER):
            raise ValueError("Unit is not permitted.")

        result = self.runner(
            ["/usr/bin/systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        state = result.stdout.strip()

        if result.returncode not in (0, 3):
            raise RuntimeError(
                f"Could not inspect systemd unit: {unit}"
            )

        if state not in (
                "active", "inactive", "failed", "activating",
                "deactivating", "reloading",
        ):
            raise RuntimeError("Unexpected systemd state.")

        return state

    def recovery_pending(self) -> bool:
        state = self._check_unit(RESTORE_TIMER)

        # Fail closed when timer state is uncertain.
        if state != "inactive":
            return True

        return False

    def demo_service_active(self) -> bool:
        return self._check_unit(DEMO_SERVICE) == "active"

    def schedule_recovery(self, deadline: str) -> None:
        raise NotImplementedError(
            "Persistent recovery scheduling is not enabled."
        )


    def verify_recovery(self, deadline: str) -> bool:
        """Check the real systemd timer against an expected UTC deadline."""

        if self._check_unit(RESTORE_TIMER) != "active":
            return False

        try:
            expected = datetime.fromisoformat(deadline)
            if expected.tzinfo is None:
                return False
            expected = expected.astimezone(timezone.utc)
        except (TypeError, ValueError, AttributeError):
            return False

        result = self.runner(
            [
                "/usr/bin/systemctl",
                "show",
                RESTORE_TIMER,
                "--property=NextElapseUSecRealtime",
                "--value",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError("Could not inspect recovery deadline.")

        try:
            actual = datetime.strptime(
                result.stdout.strip(),
                "%a %Y-%m-%d %H:%M:%S UTC",
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            return False

        return abs((actual - expected).total_seconds()) <= 2


    def stop_demo_service(self) -> None:
        raise NotImplementedError(
            "Live containment is not enabled."
        )

    def start_demo_service(self) -> None:
        raise NotImplementedError(
            "Live service control is not enabled."
        )
