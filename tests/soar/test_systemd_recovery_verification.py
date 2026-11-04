

import subprocess
import unittest
from unittest.mock import Mock

from app.soar.playbooks.systemd_backend import SystemdBackend


class TestRecoveryVerification(unittest.TestCase):

    def make_backend(self, state, schedule=None):
        responses = [
            subprocess.CompletedProcess(
                [], 0 if state == "active" else 3,
                state + "\n", "",
                )
        ]

        if schedule is not None:
            responses.append(
                subprocess.CompletedProcess(
                    [], 0, schedule + "\n", "",
                           )
            )

        runner = Mock(side_effect=responses)
        return SystemdBackend(runner=runner)

    def test_matching_recovery_deadline(self):
        backend = self.make_backend(
            "active",
            "Sun 2026-11-01 15:01:30 UTC",
        )

        self.assertTrue(
            backend.verify_recovery(
                "2026-11-01T15:01:30+00:00"
            )
        )

    def test_wrong_recovery_deadline(self):
        backend = self.make_backend(
            "active",
            "Sun 2026-11-01 23:59:00 UTC",
        )

        self.assertFalse(
            backend.verify_recovery(
                "2026-11-01T15:01:30+00:00"
            )
        )

    def test_inactive_timer_rejected(self):
        backend = self.make_backend("inactive")

        self.assertFalse(
            backend.verify_recovery(
                "2026-11-01T15:01:30+00:00"
            )
        )

    def test_invalid_deadline_rejected(self):
        backend = self.make_backend("active")

        self.assertFalse(
            backend.verify_recovery("invalid-date")
        )

    def test_timer_without_deadline_rejected(self):
        backend = self.make_backend("active", "n/a")

        self.assertFalse(
            backend.verify_recovery(
                "2026-11-01T15:01:30+00:00"
            )
        )


if __name__ == "__main__":
    unittest.main()
