
"""SOAR event classification and response selection."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Decision:
    """Result of evaluating a monitoring event."""

    event_type: str
    severity: str
    host: str
    actions: tuple[str, ...]
    reason: str


SUPPORTED_RULES = {
    "ServerDown": {
        "severity": "critical",
        "actions": ("record_incident", "notify_operator"),
    },
    "HighCPUUsage": {
        "severity": "warning",
        "actions": ("record_incident", "notify_operator"),
    },
    "HighMemoryUsage": {
        "severity": "warning",
        "actions": ("record_incident", "notify_operator"),
    },
    "SuspiciousIPDetected": {
        "severity": "critical",
        "actions": (
            "record_incident",
            "notify_operator",
            "simulate_ip_containment",
        ),
    },
}


def evaluate_event(alert: dict[str, Any]) -> Decision:
    """Evaluate an Alertmanager alert and select safe actions."""

    labels = alert.get("labels", {})

    if not isinstance(labels, dict):
        raise ValueError("Alert labels must be an object.")

    event_type = str(labels.get("alertname", "Unknown"))
    host = str(labels.get("host") or labels.get("instance") or "unknown")
    status = str(alert.get("status", "firing"))

    if status not in {"firing", "resolved"}:
        raise ValueError(f"Unsupported alert status: {status}")

    rule = SUPPORTED_RULES.get(event_type)

    if rule is None:
        return Decision(
            event_type=event_type,
            severity="info",
            host=host,
            actions=(),
            reason="Unknown event requires manual review.",
        )

    if status == "resolved":
        return Decision(
            event_type=event_type,
            severity=rule["severity"],
            host=host,
            actions=("record_incident",),
            reason="Alert resolved; record recovery without notifying again.",
        )

    return Decision(
        event_type=event_type,
        severity=rule["severity"],
        host=host,
        actions=rule["actions"],
        reason=f"Matched response rule for {event_type}.",
    )
