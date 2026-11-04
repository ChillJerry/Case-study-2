from prometheus_client import Counter, Histogram


alerts_processed = Counter(
    "soar_alerts_processed_total",
    "Total successfully processed SOAR alerts",
)

alerts_duplicates = Counter(
    "soar_alerts_duplicate_total",
    "Total duplicate SOAR alerts skipped",
)

alerts_failed = Counter(
    "soar_alerts_failed_total",
    "Total failed SOAR alert processing attempts",
)

actions_total = Counter(
    "soar_actions_total",
    "Total SOAR actions reported as completed",
    ["action_type"],
)




security_events = Counter(
    "soar_security_events_total",
    "Successfully processed security events by classification",
    ["event_type", "severity"],
)






action_outcomes = Counter(
    "soar_action_outcomes_total",
    "SOAR action attempts by type and actual outcome",
    ["action_type", "outcome"],
)


alert_processing_duration = Histogram(
    "soar_alert_processing_duration_seconds",
    "Time spent handling individual SOAR alerts",
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        float("inf"),
    ),
)
