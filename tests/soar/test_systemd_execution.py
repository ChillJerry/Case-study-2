
"""Tests for restricted systemd execution planning."""

import unittest
from datetime import datetime, timezone

from app.soar.playbooks.service_recovery import (
    RecoveryPlan,
    plan_containment,
)
from app.soar.playbooks.systemd_execution import (
    build_execution_plan,
)


class TestSystemdExecution(unittest.TestCase):

    def test_valid_execution_plan(self):
        recovery = plan_containment(
            "soar-demo.service",
            90,
            authorized=True,
            now=datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc),
        )

        result = build_execution_plan(recovery)

        self.assertTrue(result.approved)
        self.assertEqual(
            result.recovery_deadline,
            "2026-11-01 15:01:30 UTC",
        )
        self.assertEqual(
            result.containment_command,
            (
                "/usr/bin/systemctl",
                "stop",
                "soar-demo.service",
            ),
        )

    def test_rejected_request_has_no_commands(self):
        recovery = plan_containment(
            "innovatech-soar.service",
            authorized=True,
        )

        result = build_execution_plan(recovery)

        self.assertFalse(result.approved)
        self.assertEqual(result.recovery_command, ())
        self.assertEqual(result.containment_command, ())

    def test_forged_plan_cannot_target_other_services(self):
        forged = RecoveryPlan(
            approved=True,
            service="ssh.service",
            deadline="2026-11-01T15:01:30+00:00",
            reason="forged",
        )

        result = build_execution_plan(forged)

        self.assertFalse(result.approved)

    def test_invalid_deadline_is_rejected(self):
        invalid = RecoveryPlan(
            approved=True,
            service="soar-demo.service",
            deadline="not-a-date",
            reason="invalid",
        )

        result = build_execution_plan(invalid)

        self.assertFalse(result.approved)


if __name__ == "__main__":
    unittest.main()
