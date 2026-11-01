
"""SOAR incident recording and notification preparation."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.soar.rules import Decision


DATA_DIR = Path(os.environ.get("SOAR_DATA_DIR", "data/soar"))


def append_jsonl(filename: str, payload: dict) -> None:
    """Append a structured record to a local audit file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with (DATA_DIR / filename).open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload) + "\n")


def execute_actions(decision: Decision, status: str) -> list[str]:
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

    # Audit every accepted event, including unknown alerts.
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

    return executed
