

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.soar.playbooks.containment_lock import ContainmentLock
from app.soar.playbooks.live_service_executor import contain_demo_service


class FakeBackend:
    def __init__(
            self,
            *,
            pending=False,
            schedule_failure=False,
            verify_failure=False,
            stop_failure=False,
    ):
        self.calls = []
        self.pending = pending
        self.schedule_failure = schedule_failure
        self.verify_failure = verify_failure
        self.stop_failure = stop_failure

    def recovery_pending(self):
        self.calls.append("check")
        return self.pending

    def schedule_recovery(self, deadline):
        self.calls.append("schedule")
        if self.schedule_failure:
            raise RuntimeError("Timer scheduling failed")

    def verify_recovery(self, deadline):
        self.calls.append("verify")
        return not self.verify_failure

    def stop_demo_service(self):
        self.calls.append("stop")
        if self.stop_failure:
            raise RuntimeError("Service stop failed")

    def start_demo_service(self):
        self.calls.append("restore")


class TestLiveServiceExecutor(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.lock = ContainmentLock(
            str(Path(self.tempdir.name) / "containment.lock")
        )
        self.now = datetime(
            2026, 11, 1, 15, 0, tzinfo=timezone.utc
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def run_containment(self, backend, duration=90):
        return contain_demo_service(
            backend,
            self.lock,
            duration_seconds=duration,
            now=self.now,
        )

    def test_successful_containment_sequence(self):
        backend = FakeBackend()
        result = self.run_containment(backend)

        self.assertEqual(result.status, "contained")
        self.assertEqual(
            backend.calls,
            ["check", "schedule", "verify", "stop"],
        )

    def test_existing_recovery_blocks_containment(self):
        backend = FakeBackend(pending=True)
        result = self.run_containment(backend)

        self.assertEqual(result.status, "rejected")
        self.assertNotIn("stop", backend.calls)

    def test_schedule_failure_prevents_stop(self):
        backend = FakeBackend(schedule_failure=True)
        result = self.run_containment(backend)

        self.assertEqual(result.status, "failed")
        self.assertNotIn("stop", backend.calls)

    def test_unverified_recovery_prevents_stop(self):
        backend = FakeBackend(verify_failure=True)
        result = self.run_containment(backend)

        self.assertEqual(result.status, "failed")
        self.assertNotIn("stop", backend.calls)

    def test_failed_stop_attempts_immediate_restore(self):
        backend = FakeBackend(stop_failure=True)
        result = self.run_containment(backend)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            backend.calls,
            ["check", "schedule", "verify", "stop", "restore"],
        )

    def test_invalid_duration_rejected(self):
        backend = FakeBackend()
        result = self.run_containment(backend, duration=999)

        self.assertEqual(result.status, "rejected")
        self.assertEqual(backend.calls, [])

    def test_existing_lock_rejects_request(self):
        backend = FakeBackend()

        with self.lock.hold():
            result = self.run_containment(backend)

        self.assertEqual(result.status, "rejected")
        self.assertEqual(backend.calls, [])


if __name__ == "__main__":
    unittest.main()
