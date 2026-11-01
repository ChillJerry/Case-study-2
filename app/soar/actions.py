
"""SOAR incident recording and notification preparation."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.soar.playbooks.containment_executor import ContainmentExecutor
from app.soar.rules import Decision
from app.soar.playbooks.service_containment import ServiceContainmentExecutor


DATA_DIR = Path(os.environ.get("SOAR_DATA_DIR", "data/soar"))


def append_jsonl(filename: str, payload: dict) -> None:
    """Append a structured record to a local audit file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with (DATA_DIR / filename).open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload) + "\n")


def execute_actions(
        decision: Decision,
        status: str,
        alert: dict | None = None,
) -> list[str]:
    """Execute the safe actions selected by the rule engine."""
    executed = []

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": decision.event_type,
        "severity": decision.severity,
        "host": decision.host,
        "status": status,
        "reason": decision.reason,
    }

    # Audit every accepted event.
    append_jsonl("events.jsonl", event)

    for action in decision.actions:
        if action == "record_incident":
            append_jsonl("incidents.jsonl", event)
            executed.append(action)

        elif action == "notify_operator":
            append_jsonl("notifications.jsonl", {
                **event,
                "message": (
                    f"{decision.severity.upper()}: "
                    f"{decision.event_type} on {decision.host}"
                ),
            })
            executed.append(action)

        elif action == "simulate_ip_containment":
            labels = (alert or {}).get("labels", {})
            source_ip = labels.get("source_ip", "")
            target = labels.get("target", "")

            # Target authorization comes from server-side configuration.
            approved_targets = {
                item.strip()
                for item in os.environ.get(
                    "SOAR_APPROVED_CONTAINMENT_TARGETS", ""
                ).split(",")
                if item.strip()
            }

            executor = ContainmentExecutor(
                str(DATA_DIR / "containment.jsonl")
            )

            result = executor.execute(
                source_ip=source_ip,
                duration_seconds=300,
                approved_target=(
                        bool(target) and target in approved_targets
                ),
                dry_run=True,
            )

            if result["status"] == "simulated":
                executed.append(action)

        elif action == "simulate_service_containment":
            labels = (alert or {}).get("labels", {})
            service = labels.get("service", "")

            approved_services = {
                item.strip()
                for item in os.environ.get(
                    "SOAR_APPROVED_SERVICES", ""
                ).split(",")
                if item.strip()
            }

            executor = ServiceContainmentExecutor(
                str(DATA_DIR / "service_containment.jsonl")
            )

            result = executor.execute(
                service=service,
                approved_services=approved_services,
                dry_run=True,
            )

            if result["status"] == "simulated":
                executed.append(action)

    return executed
