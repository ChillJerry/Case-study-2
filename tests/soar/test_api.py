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


if __name__ == "__main__":
    unittest.main()
