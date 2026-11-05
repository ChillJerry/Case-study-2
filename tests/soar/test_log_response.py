
import unittest
from unittest.mock import patch

from app.soar.log_response import (
    build_execution_trace,
    finding_to_alert,
    run,
)
from app.soar.rules import evaluate_event


class TestLogResponse(unittest.TestCase):

    def setUp(self):
        self.finding = {
            "event_type": "PossiblePortScan",
            "classification": "Possible Port Scanning",
            "severity": "warning",
            "host": "cs2-onprem-gateway",
            "source_ip": "10.30.0.10",
            "destination_ip": "10.30.0.1",
            "blocked_attempts": 12,
            "unique_ports": 4,
            "destination_ports": [45678, 45679, 45680, 45681],
            "last_seen": "2026-11-05T11:55:09+00:00",
            "reason": "12 blocked attempts targeting 4 ports",
            "recommended_action": "Investigate source host",
        }

    def test_normalized_alert_matches_rule(self):
        alert = finding_to_alert(self.finding)
        decision = evaluate_event(alert)

        self.assertEqual(decision.event_type, "PossiblePortScan")
        self.assertEqual(decision.severity, "warning")
        self.assertEqual(
            decision.actions,
            ("record_incident", "notify_operator"),
        )

    def test_same_finding_has_stable_fingerprint(self):
        first = finding_to_alert(self.finding)
        second = finding_to_alert(self.finding)

        self.assertEqual(
            first["fingerprint"],
            second["fingerprint"],
        )

    def test_execution_trace_reports_no_containment(self):
        result = {
            "status": "processed",
            "severity": "warning",
            "actions": ["record_incident", "notify_operator"],
        }

        trace = build_execution_trace(self.finding, result)

        self.assertEqual(trace["status"], "processed")
        self.assertEqual(trace["containment"], "not_executed")
        self.assertEqual(
            trace["steps"][-1]["details"],
            ["record_incident", "notify_operator"],
        )

    @patch("app.soar.log_response.analyze_firewall")
    def test_preview_does_not_submit_alerts(self, analyzer):
        analyzer.return_value = {
            "truncated": False,
            "findings": [self.finding],
        }

        with patch(
                "app.soar.log_response.submit_alerts"
        ) as submit:
            result = run(execute=False)

        self.assertEqual(result["mode"], "preview")
        self.assertEqual(result["execution_traces"], [])
        submit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
