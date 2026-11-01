
"""Tests for restricted, read-only systemd inspection."""

import subprocess
import unittest
from unittest.mock import Mock

from app.soar.playbooks.systemd_backend import SystemdBackend


class TestSystemdBackend(unittest.TestCase):

    def test_active_timer_is_detected(self):
        runner = Mock(return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="active\n", stderr=""
        ))

        backend = SystemdBackend(runner=runner)

        self.assertTrue(backend.recovery_pending())
        self.assertEqual(
            runner.call_args.args[0],
            [
                "/usr/bin/systemctl",
                "is-active",
                "soar-demo-restore.timer",
            ],
        )

    def test_inactive_timer_is_not_pending(self):
        runner = Mock(return_value=subprocess.CompletedProcess(
            args=[], returncode=3, stdout="inactive\n", stderr=""
        ))

        backend = SystemdBackend(runner=runner)

        self.assertFalse(backend.recovery_pending())

    def test_systemd_errors_fail_closed(self):
        runner = Mock(return_value=subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="failed"
        ))

        backend = SystemdBackend(runner=runner)

        with self.assertRaises(RuntimeError):
            backend.recovery_pending()

    def test_rejects_unauthorized_unit(self):
        backend = SystemdBackend(runner=Mock())

        with self.assertRaises(ValueError):
            backend._check_unit("ssh.service")

    def test_live_control_is_disabled(self):
        backend = SystemdBackend(runner=Mock())

        with self.assertRaises(NotImplementedError):
            backend.stop_demo_service()

        with self.assertRaises(NotImplementedError):
            backend.schedule_recovery(
                "2026-11-01T15:00:00+00:00"
            )


if __name__ == "__main__":
    unittest.main()
