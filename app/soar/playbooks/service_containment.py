

import json
import re
from datetime import datetime, timezone
from pathlib import Path


SERVICE_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.@-]{0,127}$")

PROTECTED_SERVICES = {
    "ssh",
    "sshd",
    "systemd-networkd",
    "systemd-resolved",
    "NetworkManager",
    "amazon-ssm-agent",
    "snap.amazon-ssm-agent.amazon-ssm-agent",
    "wg-quick@wg0",
    "docker",
    "containerd",
    "innovatech-soar",
}


class ServiceContainmentExecutor:

    def __init__(self, audit_path: str):
        self.audit_path = Path(audit_path)

    def execute(
            self,
            service: str,
            *,
            approved_services: set[str] | None = None,
            dry_run: bool = True,
    ) -> dict:
        approved_services = approved_services or set()

        if not isinstance(service, str) or not SERVICE_PATTERN.fullmatch(service):
            status = "rejected"
            reason = "Invalid service name."

        elif service in PROTECTED_SERVICES:
            status = "rejected"
            reason = "Infrastructure service is protected."

        elif service not in approved_services:
            status = "rejected"
            reason = "Service is not explicitly approved."

        elif not dry_run:
            status = "rejected"
            reason = "Live service containment is not implemented."

        else:
            status = "simulated"
            reason = "Approved service containment simulated."

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "service_containment",
            "service": service,
            "status": status,
            "reason": reason,
            "dry_run": True,
        }

        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

        with self.audit_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(result) + "\n")

        return result
