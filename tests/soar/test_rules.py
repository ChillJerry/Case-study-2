import unittest

from app.soar.rules import evaluate_event


class TestSOARRules(unittest.TestCase):

    def test_server_down_selects_two_actions(self):
        alert = {
            "status": "firing",
            "labels": {
                "alertname": "ServerDown",
                "host": "cs2-onprem-security",
                "severity": "critical",
            },
        }

        decision = evaluate_event(alert)

        self.assertEqual(decision.event_type, "ServerDown")
        self.assertEqual(decision.severity, "critical")
        self.assertEqual(decision.host, "cs2-onprem-security")
        self.assertEqual(
            decision.actions,
            ("record_incident", "notify_operator"),
        )

    def test_high_cpu_selects_warning_response(self):
        alert = {
            "status": "firing",
            "labels": {
                "alertname": "HighCPUUsage",
                "host": "cs2-onprem-linux",
            },
        }

        decision = evaluate_event(alert)

        self.assertEqual(decision.severity, "warning")
        self.assertIn("notify_operator", decision.actions)

    def test_unknown_event_does_not_trigger_actions(self):
        alert = {
            "status": "firing",
            "labels": {
                "alertname": "UnknownSecurityEvent",
                "host": "unknown",
            },
        }

        decision = evaluate_event(alert)

        self.assertEqual(decision.actions, ())
        self.assertEqual(decision.severity, "info")

    def test_resolved_alert_records_recovery(self):
        alert = {
            "status": "resolved",
            "labels": {
                "alertname": "ServerDown",
                "host": "cs2-onprem-security",
            },
        }

        decision = evaluate_event(alert)

        self.assertEqual(decision.actions, ("record_incident",))

    def test_invalid_labels_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_event({
                "status": "firing",
                "labels": "invalid",
            })


if __name__ == "__main__":
    unittest.main()
