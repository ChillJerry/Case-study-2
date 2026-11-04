

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from deploy.soar import demo_containment_helper as helper


class TestDemoContainmentHelper(unittest.TestCase):

    def test_target_is_fixed(self):
        self.assertEqual(helper.SERVICE, "soar-demo.service")

    def test_duration_is_fixed(self):
        self.assertEqual(helper.DURATION_SECONDS, 90)

    def test_recovery_unit_is_fixed(self):
        self.assertIn(
            "ExecStart=/usr/bin/systemctl start soar-demo.service",
            helper.EXPECTED_RESTORE_SERVICE,
        )

    def test_unprivileged_execution_is_denied(self):
        with patch.object(helper, "fcntl", object()):
            with patch.object(
                    helper.os,
                    "geteuid",
                    return_value=1000,
                    create=True,
            ):
                with self.assertRaises(PermissionError):
                    helper.contain()

    def test_dry_run_does_not_execute_systemctl(self):
        output = io.StringIO()

        with patch("sys.argv", ["helper.py"]):
            with patch.object(helper, "run_systemctl") as runner:
                with redirect_stdout(output):
                    helper.main()

        runner.assert_not_called()
        self.assertIn("DRY RUN ONLY", output.getvalue())

    def test_timer_config_has_correct_deadline(self):
        from app.soar.playbooks.recovery_timer_config import (
            build_timer_configuration,
        )

        now = datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc)
        deadline = now + timedelta(seconds=90)

        config = build_timer_configuration(
            deadline.isoformat(),
            now=now,
        )

        self.assertIn(
            "OnCalendar=2026-11-01 15:01:30 UTC",
            config,
        )
        self.assertIn("Persistent=true", config)

    def run_simulated_containment(
            self,
            *,
            schedule_fails=False,
            verify_fails=False,
    ):

        calls = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            fake_fcntl = SimpleNamespace(
                LOCK_EX=2,
                LOCK_NB=4,
                flock=lambda *args: None,
            )

            def fake_systemctl(*args):
                calls.append(args)
                return ""

            def fake_install(*args):
                calls.append(("install_timer",))
                if schedule_fails:
                    raise RuntimeError("Scheduling failed")

            def fake_verify(*args):
                calls.append(("verify_timer",))
                if verify_fails:
                    raise RuntimeError("Verification failed")

            with (
                patch.object(helper, "fcntl", fake_fcntl),
                patch.object(
                    helper.os,
                    "geteuid",
                    return_value=0,
                    create=True,
                ),
                patch.object(helper, "STATE_DIR", root),
                patch.object(
                    helper,
                    "STATE_FILE",
                    root / "pending.json",
                ),
                patch.object(
                    helper,
                    "AUDIT_FILE",
                    root / "audit.jsonl",
                ),
                patch.object(
                    helper,
                    "LOCK_FILE",
                    root / "test.lock",
                ),
                patch.object(helper, "inspect_environment"),
                patch.object(
                    helper,
                    "install_timer",
                    side_effect=fake_install,
                ),
                patch.object(
                    helper,
                    "verify_timer",
                    side_effect=fake_verify,
                ),
                patch.object(
                    helper,
                    "run_systemctl",
                    side_effect=fake_systemctl,
                ),
            ):
                with redirect_stdout(io.StringIO()):
                    if schedule_fails or verify_fails:
                        with self.assertRaises(RuntimeError):
                            helper.contain()
                    else:
                        helper.contain()

                self.assertTrue(
                    (root / "pending.json").exists()
                )

        return calls

    def test_schedule_failure_never_stops_service(self):
        calls = self.run_simulated_containment(
            schedule_fails=True
        )

        self.assertNotIn(
            ("stop", "soar-demo.service"),
            calls,
        )

    def test_verification_failure_never_stops_service(self):
        calls = self.run_simulated_containment(
            verify_fails=True
        )

        self.assertNotIn(
            ("stop", "soar-demo.service"),
            calls,
        )

    def test_success_schedules_before_stopping(self):
        calls = self.run_simulated_containment()

        self.assertLess(
            calls.index(("install_timer",)),
            calls.index(("verify_timer",)),
        )

        self.assertLess(
            calls.index(("verify_timer",)),
            calls.index(("stop", "soar-demo.service")),
        )


if __name__ == "__main__":
    unittest.main()
