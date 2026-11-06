
import logging
import os

logger = logging.getLogger(__name__)


def save_execution_record(
        record_type: str,
        payload: dict,
        status_override: str | None = None,
) -> None:
    """Copy a SOAR execution record into PostgreSQL."""

    password = os.environ.get("SOAR_DB_PASSWORD")

    if not password:
        return

    try:
        import psycopg
        from psycopg.types.json import Jsonb

        with psycopg.connect(
                host=os.environ.get("SOAR_DB_HOST", "127.0.0.1"),
                port=5432,
                dbname="innovatech_soar",
                user="soar_app",
                password=password,
                connect_timeout=3,
        ) as connection:
            connection.execute(
                """
                INSERT INTO execution_records (
                    record_type,
                    event_type,
                    severity,
                    action_name,
                    status,
                    source_ip,
                    fingerprint,
                    details
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record_type,
                    payload.get("event_type"),
                    payload.get("severity"),
                    payload.get("action_name"),
                    status_override or payload.get("status"),
                    payload.get("source_ip"),
                    payload.get("fingerprint"),
                    Jsonb(payload),
                ),
            )

    except Exception as error:
        # Keep SOAR operational if PostgreSQL is unavailable.
        # The original JSONL records remain available.
        logger.warning(
            "PostgreSQL execution recording failed: %s",
            type(error).__name__,
        )
