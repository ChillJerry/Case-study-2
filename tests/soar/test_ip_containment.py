

import unittest

from app.soar.playbooks.ip_containment import (
    validate_containment,
)


class TestIPContainment(unittest.TestCase):

    def test_valid_public_ip(self):
        result = validate_containment("8.8.8.8", 300)
        self.assertTrue(result.approved)

    def test_protect_aws_infrastructure(self):
        result = validate_containment("10.20.20.10")
        self.assertFalse(result.approved)

    def test_protect_onprem_infrastructure(self):
        result = validate_containment("10.30.0.20")
        self.assertFalse(result.approved)

    def test_protect_wireguard_network(self):
        result = validate_containment("10.40.0.1")
        self.assertFalse(result.approved)

    def test_reject_invalid_ip(self):
        result = validate_containment("not-an-ip")
        self.assertFalse(result.approved)

    def test_reject_ipv6(self):
        result = validate_containment("2001:4860:4860::8888")
        self.assertFalse(result.approved)

    def test_reject_excessive_duration(self):
        result = validate_containment("8.8.8.8", 3600)
        self.assertFalse(result.approved)


if __name__ == "__main__":
    unittest.main()
