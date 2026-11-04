

from datetime import datetime, timezone

from app.soar.playbooks.service_recovery import DEMO_SERVICE


RESTORE_UNIT = "soar-demo-restore.service"


def build_timer_configuration(
        deadline: str,
        *,
        now: datetime | None = None,
) -> str:

    try:
        target = datetime.fromisoformat(deadline)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid recovery deadline.") from exc

    if target.tzinfo is None:
        raise ValueError("Deadline must have a timezone.")

    target = target.astimezone(timezone.utc)
    current = now if now is not None else datetime.now(timezone.utc)

    if current.tzinfo is None:
        raise ValueError("Current time must have a timezone.")

    remaining = (
            target - current.astimezone(timezone.utc)
    ).total_seconds()

    if not 60 <= remaining <= 300:
        raise ValueError(
            "Recovery must be scheduled 60–300 seconds ahead."
        )

    
    from datetime import timedelta

    if target.microsecond:
        target = (
                target.replace(microsecond=0) + timedelta(seconds=1)
        )

    calendar = target.strftime("%Y-%m-%d %H:%M:%S UTC")

    return (
        "[Unit]\n"
        f"Description=Persistent recovery timer for {DEMO_SERVICE}\n"
        "\n"
        "[Timer]\n"
        f"OnCalendar={calendar}\n"
        "Persistent=true\n"
        "AccuracySec=1s\n"
        f"Unit={RESTORE_UNIT}\n"
        "\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )
