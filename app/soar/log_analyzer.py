
import ipaddress
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen


LOKI_URL = os.environ.get(
    "SOAR_LOKI_URL",
    "http://10.20.10.10:3100",
).rstrip("/")

FIREWALL_QUERY = '{job="onprem-firewall"} |= "INNOVATECH_FW_DROP"'

FIELD_PATTERN = re.compile(r"(?:^|\s)(SRC|DST|PROTO|DPT)=([^\s]+)")


def parse_firewall_log(timestamp, message, host="unknown"):
    if "INNOVATECH_FW_DROP" not in message:
        return None

    fields = dict(FIELD_PATTERN.findall(message))

    if fields.get("PROTO") != "TCP":
        return None

    source_ip = fields.get("SRC")
    destination_ip = fields.get("DST")
    destination_port = fields.get("DPT")

    try:
        source = ipaddress.ip_address(source_ip)
        destination = ipaddress.ip_address(destination_ip)
        port = int(destination_port)

        if source.version != 4 or destination.version != 4:
            return None

        if not 1 <= port <= 65535:
            return None
    except (ValueError, TypeError):
        return None

    return {
        "timestamp": datetime.fromtimestamp(
            int(timestamp) / 1_000_000_000,
            timezone.utc,
            ).isoformat(),
        "host": host,
        "source_ip": str(source),
        "destination_ip": str(destination),
        "destination_port": port,
        "protocol": "TCP",
        "event_type": "firewall_drop",
        "raw_message": message,
    }


def fetch_firewall_logs(
        loki_url=LOKI_URL,
        window_seconds=300,
        limit=5000,
):
    end = time.time_ns()
    start = end - window_seconds * 1_000_000_000

    parameters = urlencode({
        "query": FIREWALL_QUERY,
        "start": str(start),
        "end": str(end),
        "limit": str(limit),
        "direction": "BACKWARD",
    })

    url = f"{loki_url}/loki/api/v1/query_range?{parameters}"

    with urlopen(url, timeout=15) as response:
        payload = json.load(response)

    if payload.get("status") != "success":
        raise ValueError("Loki returned an unsuccessful response")

    events = []
    raw_count = 0

    for stream in payload.get("data", {}).get("result", []):
        host = stream.get("stream", {}).get("host", "unknown")

        for timestamp, message in stream.get("values", []):
            raw_count += 1
            event = parse_firewall_log(timestamp, message, host)

            if event is not None:
                events.append(event)

    return {
        "events": events,
        "raw_count": raw_count,
        "truncated": raw_count >= limit,
    }


def detect_suspicious_activity(
        events,
        min_attempts=10,
        min_ports=3,
):
    groups = defaultdict(list)

    for event in events:
        key = (
            event["host"],
            event["source_ip"],
            event["destination_ip"],
        )
        groups[key].append(event)

    findings = []

    for (host, source_ip, destination_ip), group in groups.items():
        ports = sorted({
            event["destination_port"]
            for event in group
        })

        if len(group) < min_attempts or len(ports) < min_ports:
            continue

        group.sort(key=lambda event: event["timestamp"])

        findings.append({
            "event_type": "PossiblePortScan",
            "classification": "Possible Port Scanning",
            "severity": "warning",
            "host": host,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "blocked_attempts": len(group),
            "unique_ports": len(ports),
            "destination_ports": ports,
            "first_seen": group[0]["timestamp"],
            "last_seen": group[-1]["timestamp"],
            "reason": (
                f"{len(group)} blocked TCP connection attempts "
                f"targeting {len(ports)} different ports"
            ),
            "recommended_action": (
                "Investigate the source host and verify "
                "whether the connection attempts were authorized."
            ),
            "containment": "not_executed",
            "evidence": [
                event["raw_message"]
                for event in group[:3]
            ],
        })

    findings.sort(
        key=lambda finding: finding["blocked_attempts"],
        reverse=True,
    )

    return findings


def analyze_firewall(
        loki_url=LOKI_URL,
        window_seconds=300,
        min_attempts=10,
        min_ports=3,
):
    result = fetch_firewall_logs(
        loki_url=loki_url,
        window_seconds=window_seconds,
    )

    findings = detect_suspicious_activity(
        result["events"],
        min_attempts=min_attempts,
        min_ports=min_ports,
    )

    return {
        "source": "Loki",
        "log_stream": "onprem-firewall",
        "window_seconds": window_seconds,
        "raw_logs_examined": result["raw_count"],
        "normalized_tcp_events": len(result["events"]),
        "truncated": result["truncated"],
        "findings_count": len(findings),
        "findings": findings,
    }


if __name__ == "__main__":
    print(json.dumps(analyze_firewall(), indent=2))
