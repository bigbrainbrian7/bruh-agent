import sqlite3
from pathlib import Path


class StateStore:
    """Store Bruh Agent's global message-processing checkpoint."""

    def __init__(self, db_path: str | Path):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_processed_message_id INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def get_last_processed_message_id(self) -> int:
        row = self.conn.execute(
            """
            SELECT last_processed_message_id
            FROM agent_state
            WHERE id = 1
            """
        ).fetchone()

        return row[0] if row else 0

    def set_last_processed_message_id(self, message_id: int) -> None:
        self.conn.execute(
            """
            INSERT INTO agent_state (id, last_processed_message_id)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET
                last_processed_message_id = excluded.last_processed_message_id
            """,
            (message_id,),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
