
import unittest

from app.soar.log_analyzer import (
    detect_suspicious_activity,
    parse_firewall_log,
)


class TestLogAnalyzer(unittest.TestCase):

    def setUp(self):
        self.timestamp = "1793878940428840829"

    def test_parse_blocked_tcp_connection(self):
        message = (
            "kernel: INNOVATECH_FW_DROPIN=enp0s8 "
            "SRC=10.30.0.10 DST=10.30.0.1 "
            "PROTO=TCP SPT=50123 DPT=3306"
        )

        event = parse_firewall_log(
            self.timestamp,
            message,
            "cs2-onprem-gateway",
        )

        self.assertIsNotNone(event)
        self.assertEqual(event["source_ip"], "10.30.0.10")
        self.assertEqual(event["destination_port"], 3306)
        self.assertEqual(event["event_type"], "firewall_drop")

    def test_ignore_icmpv6_router_advertisement(self):
        message = (
            "kernel: INNOVATECH_FW_DROPIN=enp0s3 "
            "SRC=fe80::2 DST=ff02::1 "
            "PROTO=ICMPv6 TYPE=134 CODE=0"
        )

        event = parse_firewall_log(self.timestamp, message)

        self.assertIsNone(event)

    def test_detect_possible_port_scan(self):
        events = []

        for index in range(12):
            port = [22, 3306, 8080, 8443][index % 4]

            message = (
                "kernel: INNOVATECH_FW_DROP "
                "SRC=10.30.0.10 DST=10.30.0.1 "
                f"PROTO=TCP DPT={port}"
            )

            event = parse_firewall_log(
                str(int(self.timestamp) + index),
                message,
                "cs2-onprem-gateway",
            )

            events.append(event)

        findings = detect_suspicious_activity(events)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["blocked_attempts"], 12)
        self.assertEqual(findings[0]["unique_ports"], 4)
        self.assertEqual(
            findings[0]["classification"],
            "Possible Port Scanning",
        )
        self.assertEqual(
            findings[0]["containment"],
            "not_executed",
        )

    def test_ignore_low_volume_activity(self):
        message = (
            "INNOVATECH_FW_DROP "
            "SRC=10.30.0.10 DST=10.30.0.1 "
            "PROTO=TCP DPT=22"
        )

        event = parse_firewall_log(self.timestamp, message)

        self.assertEqual(
            detect_suspicious_activity([event]),
            [],
        )


if __name__ == "__main__":
    unittest.main()
