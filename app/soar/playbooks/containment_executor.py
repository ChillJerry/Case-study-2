import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.soar.playbooks.ip_containment import validate_containment


class ContainmentExecutor:
    def __init__(self, audit_path: str):
        self.audit_path = Path(audit_path)

    def _record(self, event: dict) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

        with self.audit_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event) + "\n")

    def execute(
            self,
            source_ip: str,
            duration_seconds: int = 300,
            *,
            approved_target: bool = False,
            dry_run: bool = True,
            now: datetime | None = None,
    ) -> dict:

        timestamp = now or datetime.now(timezone.utc)

        decision = validate_containment(
            source_ip, duration_seconds
        )

        if not decision.approved:
            status = "rejected"
            reason = decision.reason
        elif not approved_target:
            status = "rejected"
            reason = "Containment target is not authorized."
        elif not dry_run:
            status = "rejected"
            reason = "Live enforcement is not implemented."
        else:
            status = "simulated"
            reason = "Dry-run containment approved."

        result = {
            "timestamp": timestamp.isoformat(),
            "action": "temporary_ip_containment",
            "source_ip": source_ip,
            "duration_seconds": duration_seconds,
            "status": status,
            "reason": reason,
            "dry_run": True,
            "expires_at": (
                (timestamp + timedelta(seconds=duration_seconds))
                .isoformat()
                if status == "simulated"
                else None
            ),
        }

        self._record(result)
        return result
