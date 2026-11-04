

import tempfile
import unittest
from pathlib import Path

from app.soar.dedup import AlertStore


class TestAlertStore(unittest.TestCase):

    def test_new_alert_is_not_processed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AlertStore(
                str(Path(directory) / "alerts.db")
            )

            self.assertFalse(
                store.is_processed("abc123", "firing")
            )

    def test_processed_alert_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AlertStore(
                str(Path(directory) / "alerts.db")
            )

            store.mark_processed("abc123", "firing")

            self.assertTrue(
                store.is_processed("abc123", "firing")
            )

    def test_different_status_is_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AlertStore(
                str(Path(directory) / "alerts.db")
            )

            store.mark_processed("abc123", "firing")

            self.assertFalse(
                store.is_processed("abc123", "resolved")
            )

    def test_data_survives_new_store_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "alerts.db")

            store = AlertStore(path)
            store.mark_processed("abc123", "firing")

            reopened = AlertStore(path)

            self.assertTrue(
                reopened.is_processed("abc123", "firing")
            )


if __name__ == "__main__":
    unittest.main()
