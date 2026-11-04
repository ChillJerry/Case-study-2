

import unittest
from datetime import datetime, timezone, timedelta

from app.soar.playbooks.service_recovery import RecoveryPlan
from app.soar.playbooks.recovery_guard import check_recovery_safety


class TestRecoveryGuard(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 1, 15, 0, tzinfo=timezone.utc
        )

    def make_plan(self, seconds=90, service="soar-demo.service"):
        return RecoveryPlan(
            approved=True,
            service=service,
            deadline=(
                    self.now + timedelta(seconds=seconds)
            ).isoformat(),
            reason="test",
        )

    def test_valid_recovery(self):
        result = check_recovery_safety(
            self.make_plan(),
            existing_recovery=False,
            now=self.now,
        )
        self.assertTrue(result.approved)

    def test_rejects_expired_deadline(self):
        result = check_recovery_safety(
            self.make_plan(-10),
            existing_recovery=False,
            now=self.now,
        )
        self.assertFalse(result.approved)

    def test_rejects_excessive_duration(self):
        result = check_recovery_safety(
            self.make_plan(3600),
            existing_recovery=False,
            now=self.now,
        )
        self.assertFalse(result.approved)

    def test_rejects_existing_recovery(self):
        result = check_recovery_safety(
            self.make_plan(),
            existing_recovery=True,
            now=self.now,
        )
        self.assertFalse(result.approved)

    def test_rejects_critical_service(self):
        result = check_recovery_safety(
            self.make_plan(service="innovatech-soar.service"),
            existing_recovery=False,
            now=self.now,
        )
        self.assertFalse(result.approved)

    def test_rejects_unapproved_plan(self):
        plan = RecoveryPlan(
            approved=False,
            service="soar-demo.service",
            deadline=(self.now + timedelta(seconds=90)).isoformat(),
            reason="rejected",
        )

        result = check_recovery_safety(
            plan,
            existing_recovery=False,
            now=self.now,
        )
        self.assertFalse(result.approved)


if __name__ == "__main__":
    unittest.main()
