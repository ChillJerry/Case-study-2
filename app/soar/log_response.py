
import argparse
import hashlib
import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.soar.log_analyzer import analyze_firewall


SOAR_URL = os.environ.get(
    "SOAR_API_URL",
    "http://10.20.20.10:8000",
).rstrip("/")


def finding_to_alert(finding, window_seconds=300):
    last_seen = datetime.fromisoformat(finding["last_seen"])
    bucket = int(last_seen.timestamp()) // window_seconds

    identity = "|".join([
        finding["host"],
        finding["source_ip"],
        finding["destination_ip"],
        str(bucket),
    ])

    fingerprint = hashlib.sha256(identity.encode()).hexdigest()

    return {
        "status": "firing",
        "fingerprint": fingerprint,
        "labels": {
            "alertname": "PossiblePortScan",
            "host": finding["host"],
            "source_ip": finding["source_ip"],
            "destination_ip": finding["destination_ip"],
        },
        "annotations": {
            "summary": finding["classification"],
            "description": finding["reason"],
            "recommended_action": finding["recommended_action"],
            "blocked_attempts": str(finding["blocked_attempts"]),
            "destination_ports": ",".join(
                str(port) for port in finding["destination_ports"]
            ),
            "log_source": "Loki/onprem-firewall",
        },
    }


def submit_alerts(alerts, token, soar_url=SOAR_URL):
    body = json.dumps({"alerts": alerts}).encode("utf-8")

    request = Request(
        f"{soar_url}/alerts",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-SOAR-Token": token,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"SOAR rejected the request: HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"SOAR API connection failed: {error}"
        ) from error


def build_execution_trace(finding, result):
    status = result.get("status", "unknown")
    actions = result.get("actions", [])

    return {
        "source_ip": finding["source_ip"],
        "destination_ip": finding["destination_ip"],
        "classification": finding["classification"],
        "severity": result.get("severity", finding["severity"]),
        "status": status,
        "steps": [
            {
                "step": "Loki log collection",
                "status": "completed",
                "details": "Firewall records retrieved from Loki",
            },
            {
                "step": "Log normalization",
                "status": "completed",
                "details": (
                    f"{finding['blocked_attempts']} blocked TCP attempts "
                    f"across {finding['unique_ports']} ports"
                ),
            },
            {
                "step": "Security rule evaluation",
                "status": "completed",
                "details": "PossiblePortScan rule selected",
            },
            {
                "step": "SOAR processing",
                "status": status,
                "details": "Existing authenticated SOAR API",
            },
            {
                "step": "Response actions",
                "status": (
                    "duplicate" if status == "duplicate"
                    else "completed" if status == "processed"
                    else "unknown"
                ),
                "details": actions,
            },
        ],
        "containment": "not_executed",
    }


def run(execute=False, window_seconds=300):
    analysis = analyze_firewall(window_seconds=window_seconds)

    output = {
        "mode": "execute" if execute else "preview",
        "analysis": analysis,
        "execution_traces": [],
    }

    if not execute:
        return output

    if analysis["truncated"]:
        raise RuntimeError(
            "Loki query reached its result limit; refusing partial analysis"
        )

    token = os.environ.get("SOAR_WEBHOOK_TOKEN")

    if not token:
        raise RuntimeError("SOAR_WEBHOOK_TOKEN is not configured")

    findings = analysis["findings"]

    if not findings:
        return output

    for index in range(0, len(findings), 100):
        batch = findings[index:index + 100]
        alerts = [
            finding_to_alert(finding, window_seconds)
            for finding in batch
        ]

        response = submit_alerts(alerts, token)
        results = response.get("results", [])

        if response.get("status") != "completed":
            raise RuntimeError("SOAR did not complete alert processing")

        if len(results) != len(batch):
            raise RuntimeError("SOAR returned an unexpected result count")

        for finding, result in zip(batch, results):
            output["execution_traces"].append(
                build_execution_trace(finding, result)
            )

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--window", type=int, default=300)
    args = parser.parse_args()

    if not 1 <= args.window <= 86400:
        parser.error("Window must be between 1 and 86400 seconds")

    result = run(
        execute=args.execute,
        window_seconds=args.window,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
