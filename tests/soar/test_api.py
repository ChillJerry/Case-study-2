import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.soar import actions
from app.soar.main import app


class TestSOARAPI(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_data_dir = actions.DATA_DIR
        actions.DATA_DIR = Path(self.tempdir.name)

        self.token_patch = patch.dict(
            os.environ,
            {"SOAR_WEBHOOK_TOKEN": "test-secret"},
        )
        self.token_patch.start()

        self.client = app.test_client()

    def tearDown(self):
        actions.DATA_DIR = self.original_data_dir
        self.token_patch.stop()
        self.tempdir.cleanup()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_rejects_unauthorized_request(self):
        response = self.client.post("/alerts", json={
            "alerts": [{"status": "firing", "labels": {
                "alertname": "ServerDown"
            }}]
        })
        self.assertEqual(response.status_code, 401)

    def test_processes_server_down(self):
        response = self.client.post(
            "/alerts",
            headers={"X-SOAR-Token": "test-secret"},
            json={
                "alerts": [{
                    "status": "firing",
                    "labels": {
                        "alertname": "ServerDown",
                        "instance": "10.30.0.20:9100",
                    },
                }]
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["count"], 1)
        self.assertEqual(
            response.json["results"][0]["actions"],
            ["record_incident", "notify_operator"],
        )

        self.assertTrue(
            (actions.DATA_DIR / "incidents.jsonl").exists()
        )
        self.assertTrue(
            (actions.DATA_DIR / "notifications.jsonl").exists()
        )

    def test_rejects_invalid_alerts(self):
        response = self.client.post(
            "/alerts",
            headers={"X-SOAR-Token": "test-secret"},
            json={"alerts": "invalid"},
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_alert_is_skipped(self):
        payload = {
            "alerts": [{
                "status": "firing",
                "fingerprint": "server-123",
                "startsAt": "2026-11-01T10:00:00Z",
                "labels": {
                    "alertname": "ServerDown",
                    "instance": "10.30.0.20:9100",
                },
            }]
        }

        headers = {"X-SOAR-Token": "test-secret"}

        first = self.client.post(
            "/alerts", headers=headers, json=payload
        )
        second = self.client.post(
            "/alerts", headers=headers, json=payload
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            first.json["results"][0]["status"],
            "processed",
        )
        self.assertEqual(
            second.json["results"][0]["status"],
            "duplicate",
        )
        self.assertEqual(
            second.json["results"][0]["actions"],
            [],
        )

        notifications = (
                actions.DATA_DIR / "notifications.jsonl"
        ).read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(notifications), 1)

    def test_new_alert_occurrence_is_processed(self):
        headers = {"X-SOAR-Token": "test-secret"}

        def send_alert(start_time):
            return self.client.post(
                "/alerts",
                headers=headers,
                json={
                    "alerts": [{
                        "status": "firing",
                        "fingerprint": "server-123",
                        "startsAt": start_time,
                        "labels": {
                            "alertname": "ServerDown",
                            "instance": "10.30.0.20:9100",
                        },
                    }]
                },
            )

        first = send_alert("2026-11-01T10:00:00Z")
        second = send_alert("2026-11-01T12:00:00Z")

        self.assertEqual(
            first.json["results"][0]["status"],
            "processed",
        )
        self.assertEqual(
            second.json["results"][0]["status"],
            "processed",
        )

if __name__ == "__main__":
    unittest.main()
