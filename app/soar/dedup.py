import sqlite3
from contextlib import closing
from pathlib import Path


class AlertStore:

    def __init__(self, database_path: str):
        self.database_path = database_path

        Path(database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with closing(self._connect()) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS processed_alerts (
                    fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    PRIMARY KEY (fingerprint, status)
                )
            """)
            connection.commit()

    def _connect(self):
        return sqlite3.connect(self.database_path, timeout=10)

    def is_processed(self, fingerprint: str, status: str) -> bool:
        with closing(self._connect()) as connection:
            result = connection.execute(
                """
                SELECT 1 FROM processed_alerts
                WHERE fingerprint = ? AND status = ?
                """,
                (fingerprint, status),
            ).fetchone()

            return result is not None

    def mark_processed(self, fingerprint: str, status: str):
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO processed_alerts
                (fingerprint, status)
                VALUES (?, ?)
                """,
                (fingerprint, status),
            )
            connection.commit()
