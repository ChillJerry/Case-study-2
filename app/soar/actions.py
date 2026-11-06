
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.soar.metrics import action_outcomes
from app.soar.postgres_store import save_execution_record
from app.soar.playbooks.containment_executor import ContainmentExecutor
from app.soar.playbooks.service_containment import (
    ServiceContainmentExecutor,
)
from app.soar.rules import Decision


DATA_DIR = Path(os.environ.get("SOAR_DATA_DIR", "data/soar"))


def append_jsonl(filename: str, payload: dict) -> None:
    """Save a record to JSONL and PostgreSQL."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Keep the existing JSONL recording.
    with (DATA_DIR / filename).open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload) + "\n")

    # Copy supported records to PostgreSQL.
    record_types = {
        "events.jsonl": "event",
        "incidents.jsonl": "incident",
        "notifications.jsonl": "notification",
        "actions.jsonl": "action",
    }

    status_overrides = {
        "incidents.jsonl": "recorded",
        "notifications.jsonl": "prepared",
    }

    if filename in record_types:
        save_execution_record(
            record_type=record_types[filename],
            payload=payload,
            status_override=status_overrides.get(filename),
        )


def record_outcome(action_type: str, outcome: str) -> None:
    """Update the existing Prometheus action metrics."""
    action_outcomes.labels(
        action_type=action_type,
        outcome=outcome,
    ).inc()


def execute_actions(
        decision: Decision,
        status: str,
        alert: dict | None = None,
) -> list[str]:
    """Execute SOAR actions and record their outcomes."""

    executed = []

    labels = (alert or {}).get("labels") or {}
    if not isinstance(labels, dict):
        labels = {}

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": decision.event_type,
        "severity": decision.severity,
        "host": decision.host,
        "status": status,
        "reason": decision.reason,
        "source_ip": labels.get("source_ip"),
        "fingerprint": (alert or {}).get("fingerprint"),
    }

    def record_action(action_name: str, outcome: str) -> None:
        """Record action results in Prometheus, JSONL and PostgreSQL."""

        record_outcome(action_name, outcome)

        append_jsonl(
            "actions.jsonl",
            {
                **event,
                "action_name": action_name,
                "status": outcome,
            },
        )

    # Record the incoming event.
    append_jsonl("events.jsonl", event)

    for action in decision.actions:
        try:
            if action == "record_incident":
                append_jsonl("incidents.jsonl", event)

                executed.append(action)
                record_action(action, "success")

            elif action == "notify_operator":
                notification = {
                    **event,
                    "message": (
                        f"{decision.severity.upper()}: "
                        f"{decision.event_type} on {decision.host}"
                    ),
                }

                append_jsonl("notifications.jsonl", notification)

                executed.append(action)
                record_action(action, "success")

            elif action == "simulate_ip_containment":
                source_ip = labels.get("source_ip", "")
                target = labels.get("target", "")

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
                            bool(target)
                            and target in approved_targets
                    ),
                    dry_run=True,
                )

                if result["status"] == "simulated":
                    executed.append(action)
                    record_action(action, "simulated")
                else:
                    record_action(action, "rejected")

            elif action == "simulate_service_containment":
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
                    record_action(action, "simulated")
                else:
                    record_action(action, "rejected")

            else:
                record_action(action, "rejected")

        except Exception:
            record_action(action, "failed")
            raise

    return executed
