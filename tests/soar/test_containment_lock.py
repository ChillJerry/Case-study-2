
"""Tests for exclusive containment operation locking."""

import tempfile
import unittest
from pathlib import Path

from app.soar.playbooks.containment_lock import (
    ContainmentBusyError,
    ContainmentLock,
)


class TestContainmentLock(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = str(
            Path(self.tempdir.name) / "containment.lock"
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_lock_can_be_acquired(self):
        lock = ContainmentLock(self.path)
        lock.acquire()

        self.assertTrue(Path(self.path).is_dir())
        lock.release()

    def test_second_request_is_rejected(self):
        first = ContainmentLock(self.path)
        second = ContainmentLock(self.path)

        first.acquire()

        with self.assertRaises(ContainmentBusyError):
            second.acquire()

        first.release()

    def test_lock_released_after_success(self):
        lock = ContainmentLock(self.path)

        with lock.hold():
            self.assertTrue(Path(self.path).exists())

        self.assertFalse(Path(self.path).exists())

    def test_lock_released_after_exception(self):
        lock = ContainmentLock(self.path)

        with self.assertRaises(RuntimeError):
            with lock.hold():
                raise RuntimeError("Simulated execution failure")

        self.assertFalse(Path(self.path).exists())

    def test_stale_lock_fails_closed(self):
        Path(self.path).mkdir()

        lock = ContainmentLock(self.path)

        with self.assertRaises(ContainmentBusyError):
            lock.acquire()


if __name__ == "__main__":
    unittest.main()
