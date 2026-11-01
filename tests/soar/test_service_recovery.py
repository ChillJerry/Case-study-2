
"""Tests for the disposable service recovery planner."""

import unittest
from datetime import datetime, timezone

from app.soar.playbooks.service_recovery import plan_containment


class TestServiceRecovery(unittest.TestCase):

    def test_approved_demo_service(self):
        result = plan_containment(
            "soar-demo.service",
            90,
            authorized=True,
            now=datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc),
        )

        self.assertTrue(result.approved)
        self.assertEqual(
            result.deadline,
            "2026-11-01T15:01:30+00:00",
        )

    def test_rejects_critical_service(self):
        result = plan_containment(
            "innovatech-soar.service",
            authorized=True,
        )
        self.assertFalse(result.approved)

    def test_rejects_unauthorized_request(self):
        result = plan_containment("soar-demo.service")
        self.assertFalse(result.approved)

    def test_rejects_duplicate_pending_recovery(self):
        result = plan_containment(
            "soar-demo.service",
            authorized=True,
            pending_recovery=True,
        )
        self.assertFalse(result.approved)

    def test_rejects_excessive_duration(self):
        result = plan_containment(
            "soar-demo.service",
            3600,
            authorized=True,
        )
        self.assertFalse(result.approved)

    def test_rejects_short_duration(self):
        result = plan_containment(
            "soar-demo.service",
            10,
            authorized=True,
        )
        self.assertFalse(result.approved)

    def test_rejects_naive_timestamp(self):
        result = plan_containment(
            "soar-demo.service",
            authorized=True,
            now=datetime(2026, 11, 1, 15, 0),
        )
        self.assertFalse(result.approved)


if __name__ == "__main__":
    unittest.main()
