

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.soar import actions
from app.soar.rules import evaluate_event


class TestPlaybookIntegration(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_dir = actions.DATA_DIR
        actions.DATA_DIR = Path(self.tempdir.name)

    def tearDown(self):
        actions.DATA_DIR = self.original_dir
        self.tempdir.cleanup()

    def make_alert(self, source_ip, target="test-node"):
        return {
            "status": "firing",
            "labels": {
                "alertname": "SuspiciousIPDetected",
                "source_ip": source_ip,
                "target": target,
            },
        }

    def test_security_alert_selects_playbook(self):
        decision = evaluate_event(
            self.make_alert("8.8.8.8")
        )
        self.assertIn(
            "simulate_ip_containment",
            decision.actions,
        )

    def test_authorized_containment_is_simulated(self):
        alert = self.make_alert("8.8.8.8")
        decision = evaluate_event(alert)

        with patch.dict(
                os.environ,
                {"SOAR_APPROVED_CONTAINMENT_TARGETS": "test-node"},
        ):
            result = actions.execute_actions(
                decision, "firing", alert
            )

        self.assertIn("simulate_ip_containment", result)
        self.assertTrue(
            (actions.DATA_DIR / "containment.jsonl").exists()
        )

    def test_unapproved_target_is_rejected(self):
        alert = self.make_alert(
            "8.8.8.8", target="production-node"
        )
        decision = evaluate_event(alert)

        with patch.dict(
                os.environ,
                {"SOAR_APPROVED_CONTAINMENT_TARGETS": "test-node"},
        ):
            result = actions.execute_actions(
                decision, "firing", alert
            )

        self.assertNotIn(
            "simulate_ip_containment", result
        )


if __name__ == "__main__":
    unittest.main()
