

import unittest
from datetime import datetime, timedelta, timezone

from app.soar.playbooks.recovery_timer_config import (
    build_timer_configuration,
)


class TestRecoveryTimerConfig(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 1, 15, 0, tzinfo=timezone.utc
        )

    def deadline(self, seconds):
        return (
                self.now + timedelta(seconds=seconds)
        ).isoformat()

    def test_valid_timer(self):
        result = build_timer_configuration(
            self.deadline(90), now=self.now
        )

        self.assertIn(
            "OnCalendar=2026-11-01 15:01:30 UTC",
            result,
        )
        self.assertIn("Persistent=true", result)
        self.assertIn(
            "Unit=soar-demo-restore.service", result
        )

    def test_expired_deadline_rejected(self):
        with self.assertRaises(ValueError):
            build_timer_configuration(
                self.deadline(-10), now=self.now
            )

    def test_excessive_deadline_rejected(self):
        with self.assertRaises(ValueError):
            build_timer_configuration(
                self.deadline(600), now=self.now
            )

    def test_naive_deadline_rejected(self):
        with self.assertRaises(ValueError):
            build_timer_configuration(
                "2026-11-01T15:01:30",
                now=self.now,
            )

    def test_fractional_deadline_rounds_up(self):
        target = (
                self.now + timedelta(seconds=90, milliseconds=500)
        )

        result = build_timer_configuration(
            target.isoformat(), now=self.now
        )

        self.assertIn(
            "OnCalendar=2026-11-01 15:01:31 UTC",
            result,
        )


if __name__ == "__main__":
    unittest.main()
