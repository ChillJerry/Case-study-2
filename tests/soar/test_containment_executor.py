

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.soar.playbooks.containment_executor import (
    ContainmentExecutor,
)


class TestContainmentExecutor(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.audit_path = str(
            Path(self.tempdir.name) / "containment.jsonl"
        )
        self.executor = ContainmentExecutor(self.audit_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_authorized_dry_run(self):
        now = datetime(2026, 11, 1, tzinfo=timezone.utc)

        result = self.executor.execute(
            "8.8.8.8",
            300,
            approved_target=True,
            now=now,
        )

        self.assertEqual(result["status"], "simulated")
        self.assertEqual(
            result["expires_at"],
            "2026-11-01T00:05:00+00:00",
        )

    def test_rejects_protected_infrastructure(self):
        result = self.executor.execute(
            "10.20.20.10",
            approved_target=True,
        )

        self.assertEqual(result["status"], "rejected")

    def test_rejects_unauthorized_target(self):
        result = self.executor.execute("8.8.8.8")

        self.assertEqual(result["status"], "rejected")

    def test_rejects_live_enforcement(self):
        result = self.executor.execute(
            "8.8.8.8",
            approved_target=True,
            dry_run=False,
        )

        self.assertEqual(result["status"], "rejected")

    def test_writes_audit_record(self):
        self.executor.execute(
            "8.8.8.8",
            approved_target=True,
        )

        self.assertTrue(Path(self.audit_path).exists())
        self.assertEqual(
            len(Path(self.audit_path).read_text().splitlines()),
            1,
        )


if __name__ == "__main__":
    unittest.main()
