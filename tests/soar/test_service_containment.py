
"""Tests for suspicious-service containment."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.soar import actions
from app.soar.playbooks.service_containment import ServiceContainmentExecutor
from app.soar.rules import evaluate_event


class TestServiceContainment(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_dir = actions.DATA_DIR
        actions.DATA_DIR = Path(self.tempdir.name)

        self.executor = ServiceContainmentExecutor(
            str(actions.DATA_DIR / "service_containment.jsonl")
        )

    def tearDown(self):
        actions.DATA_DIR = self.original_dir
        self.tempdir.cleanup()

    def test_approved_service_is_simulated(self):
        result = self.executor.execute(
            "soar-demo.service",
            approved_services={"soar-demo.service"},
        )
        self.assertEqual(result["status"], "simulated")

    def test_unapproved_service_is_rejected(self):
        result = self.executor.execute(
            "unknown.service",
            approved_services={"soar-demo.service"},
        )
        self.assertEqual(result["status"], "rejected")

    def test_infrastructure_service_is_protected(self):
        result = self.executor.execute(
            "innovatech-soar",
            approved_services={"innovatech-soar"},
        )
        self.assertEqual(result["status"], "rejected")

    def test_live_execution_is_disabled(self):
        result = self.executor.execute(
            "soar-demo.service",
            approved_services={"soar-demo.service"},
            dry_run=False,
        )
        self.assertEqual(result["status"], "rejected")

    def test_invalid_service_name_is_rejected(self):
        result = self.executor.execute(
            "../dangerous;command",
            approved_services={"../dangerous;command"},
        )
        self.assertEqual(result["status"], "rejected")

    def test_rule_engine_selects_service_playbook(self):
        alert = {
            "status": "firing",
            "labels": {
                "alertname": "SuspiciousServiceDetected",
                "service": "soar-demo.service",
            },
        }

        decision = evaluate_event(alert)

        self.assertIn(
            "simulate_service_containment",
            decision.actions,
        )

    def test_integration_records_simulated_action(self):
        alert = {
            "status": "firing",
            "labels": {
                "alertname": "SuspiciousServiceDetected",
                "service": "soar-demo.service",
            },
        }

        decision = evaluate_event(alert)

        with patch.dict(
                os.environ,
                {"SOAR_APPROVED_SERVICES": "soar-demo.service"},
        ):
            executed = actions.execute_actions(
                decision, "firing", alert
            )

        self.assertIn("simulate_service_containment", executed)

        audit_path = actions.DATA_DIR / "service_containment.jsonl"
        records = [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
        ]

        self.assertEqual(records[0]["status"], "simulated")


if __name__ == "__main__":
    unittest.main()
