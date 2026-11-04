

import unittest

from app.soar.playbooks.privileged_policy import (
    validate_privileged_request,
)


class TestPrivilegedPolicy(unittest.TestCase):

    def test_disposable_service_is_permitted(self):
        result = validate_privileged_request(
            "contain", "soar-demo.service", 90
        )
        self.assertTrue(result.approved)

    def test_rejects_soar_service(self):
        result = validate_privileged_request(
            "contain", "innovatech-soar.service", 90
        )
        self.assertFalse(result.approved)

    def test_rejects_ssh_service(self):
        result = validate_privileged_request(
            "contain", "ssh.service", 90
        )
        self.assertFalse(result.approved)

    def test_rejects_unsupported_operation(self):
        result = validate_privileged_request(
            "restart", "soar-demo.service", 90
        )
        self.assertFalse(result.approved)

    def test_rejects_invalid_duration(self):
        for duration in (0, 301, True, "90"):
            with self.subTest(duration=duration):
                result = validate_privileged_request(
                    "contain", "soar-demo.service", duration
                )
                self.assertFalse(result.approved)


if __name__ == "__main__":
    unittest.main()
