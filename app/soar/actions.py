import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.soar.metrics import action_outcomes
from app.soar.playbooks.containment_executor import ContainmentExecutor
from app.soar.playbooks.service_containment import (
    ServiceContainmentExecutor,
)
from app.soar.rules import Decision


DATA_DIR = Path(os.environ.get("SOAR_DATA_DIR", "data/soar"))


def append_jsonl(filename: str, payload: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with (DATA_DIR / filename).open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload) + "\n")


def record_outcome(action_type: str, outcome: str) -> None:
    action_outcomes.labels(
        action_type=action_type,
        outcome=outcome,
    ).inc()


def execute_actions(
        decision: Decision,
        status: str,
        alert: dict | None = None,
) -> list[str]:

    executed = []

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": decision.event_type,
        "severity": decision.severity,
        "host": decision.host,
        "status": status,
        "reason": decision.reason,
    }

    
    append_jsonl("events.jsonl", event)

    for action in decision.actions:
        try:
            if action == "record_incident":
                append_jsonl("incidents.jsonl", event)

                executed.append(action)
                record_outcome(action, "success")

            elif action == "notify_operator":
                append_jsonl("notifications.jsonl", {
                    **event,
                    "message": (
                        f"{decision.severity.upper()}: "
                        f"{decision.event_type} on {decision.host}"
                    ),
                })

                executed.append(action)
                record_outcome(action, "success")

            elif action == "simulate_ip_containment":
                labels = (alert or {}).get("labels", {})
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
                    record_outcome(action, "simulated")
                else:
                    
                    record_outcome(action, "rejected")

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
                    record_outcome(action, "simulated")
                else:
                    record_outcome(action, "rejected")

            else:
                
                record_outcome(action, "rejected")

        except Exception:
            
            
            record_outcome(action, "failed")
            raise

    return executed
