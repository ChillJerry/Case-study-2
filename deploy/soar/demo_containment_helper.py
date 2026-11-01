
"""Root-only containment helper for the disposable SOAR demo service.

Usage:
    python3 demo_containment_helper.py
    sudo python3 demo_containment_helper.py --execute

Default mode never changes systemd.
The live mode is for an administrator-controlled lab test only.
"""

import argparse
try:
    import fcntl
except ImportError:
    fcntl = None
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.soar.playbooks.recovery_timer_config import (
    build_timer_configuration,
)

SERVICE = "soar-demo.service"
RESTORE_SERVICE = "soar-demo-restore.service"
RESTORE_TIMER = "soar-demo-restore.timer"

TIMER_FILE = Path("/etc/systemd/system") / RESTORE_TIMER
RESTORE_FILE = Path("/etc/systemd/system") / RESTORE_SERVICE
STATE_DIR = Path("/var/lib/innovatech-soar-helper")
STATE_FILE = STATE_DIR / "pending.json"
AUDIT_FILE = STATE_DIR / "audit.jsonl"
LOCK_FILE = Path("/run/lock/soar-demo-containment.lock")

DURATION_SECONDS = 90

EXPECTED_RESTORE_SERVICE = (
    "[Unit]\n"
    "Description=Restore disposable SOAR demo service\n"
    "[Service]\n"
    "Type=oneshot\n"
    "ExecStart=/usr/bin/systemctl start soar-demo.service\n"
)


def run_systemctl(*args):
    """Run only fixed systemctl commands without a shell."""
    result = subprocess.run(
        ["/usr/bin/systemctl", *args],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"systemctl {args[0]} failed: {result.stderr.strip()}"
        )

    return result.stdout.strip()


def audit(event, **details):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **details,
    }

    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    with AUDIT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def inspect_environment():
    """Reject altered recovery units or an unexpected service state."""
    if not RESTORE_FILE.is_file():
        raise RuntimeError("Recovery service is missing.")

    if RESTORE_FILE.read_text(encoding="utf-8") != EXPECTED_RESTORE_SERVICE:
        raise RuntimeError("Recovery service configuration differs.")

    if run_systemctl("is-active", SERVICE) != "active":
        raise RuntimeError("Disposable service must be active.")

    # Treat any previously scheduled recovery as pending,
    # regardless of whether its timer is currently active.
    if STATE_FILE.exists():
        raise RuntimeError(
            "Previous containment requires administrator inspection."
        )

    timer_state = subprocess.run(
        ["/usr/bin/systemctl", "is-active", RESTORE_TIMER],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    ).stdout.strip()

    if timer_state != "inactive":
        raise RuntimeError(
            f"Recovery timer is not inactive: {timer_state}"
        )


def install_timer(deadline, current_time):
    """Write the recovery timer atomically, then activate it."""
    config = build_timer_configuration(
        deadline.isoformat(),
        now=current_time,
    )

    temporary = TIMER_FILE.with_name(TIMER_FILE.name + ".tmp")

    # Root owns the destination directory in the deployment.
    with temporary.open("w", encoding="utf-8") as file:
        file.write(config)
        file.flush()
        os.fsync(file.fileno())

    os.chmod(temporary, 0o644)
    os.replace(temporary, TIMER_FILE)

    run_systemctl("daemon-reload")
    run_systemctl("enable", RESTORE_TIMER)
    run_systemctl("start", RESTORE_TIMER)


def verify_timer(deadline):
    """Verify activation, boot enablement, and actual deadline."""
    if run_systemctl("is-active", RESTORE_TIMER) != "active":
        raise RuntimeError("Recovery timer is not active.")

    if run_systemctl("is-enabled", RESTORE_TIMER) != "enabled":
        raise RuntimeError("Recovery timer is not boot-enabled.")

    output = run_systemctl(
        "show",
        RESTORE_TIMER,
        "--property=NextElapseUSecRealtime",
        "--value",
    )

    try:
        scheduled = datetime.strptime(
            output,
            "%a %Y-%m-%d %H:%M:%S UTC",
        ).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise RuntimeError(
            f"Cannot verify systemd deadline: {output}"
        ) from exc

    # Calendar deadlines have second precision.
    difference = (scheduled - deadline).total_seconds()

    if not 0 <= difference <= 2:
        raise RuntimeError("Systemd recovery deadline does not match.")


def contain():
    if fcntl is None or not hasattr(os, "geteuid"):
        raise RuntimeError(
            "Live containment is supported only on Linux."
        )

    if os.geteuid() != 0:
        raise PermissionError("Live operation requires root.")

    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE_DIR, 0o700)

    with LOCK_FILE.open("a+") as lock:
        try:
            fcntl.flock(
                lock.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
        except BlockingIOError as exc:
            raise RuntimeError(
                "Another containment operation is running."
            ) from exc

        inspect_environment()

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(seconds=DURATION_SECONDS)

        # Persist a pending marker BEFORE modifying systemd.
        # A failure leaves the marker for administrator inspection.
        with STATE_FILE.open("x", encoding="utf-8") as file:
            json.dump({
                "service": SERVICE,
                "deadline": deadline.isoformat(),
                "status": "scheduling",
            }, file)
            file.flush()
            os.fsync(file.fileno())

        audit("recovery_scheduling_started",
              deadline=deadline.isoformat())

        try:
            install_timer(deadline, now)
            verify_timer(deadline)

            audit("recovery_verified",
                  deadline=deadline.isoformat())

            # Only after verified recovery scheduling:
            run_systemctl("stop", SERVICE)

            audit("service_contained", service=SERVICE)
            print("CONTAINED: disposable service stopped.")
            print("Recovery deadline:", deadline.isoformat())

        except Exception:
            audit("containment_failed")

            # If stopping partially succeeded, attempt restoration.
            try:
                run_systemctl("start", SERVICE)
                audit("immediate_restoration_attempted")
            except Exception:
                audit("immediate_restoration_failed")

            # Keep the pending marker and any recovery timer
            # for manual inspection. Do not cancel recovery.
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform one root-authorized lab containment test",
    )
    args = parser.parse_args()

    if not args.execute:
        print("DRY RUN ONLY")
        print("Target:", SERVICE)
        print("Duration:", DURATION_SECONDS, "seconds")
        print("No systemd commands executed.")
        return

    contain()


if __name__ == "__main__":
    main()
