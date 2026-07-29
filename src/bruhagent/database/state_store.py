import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..models import Plan


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
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                chat_id TEXT PRIMARY KEY,
                plan TEXT,
                status TEXT NOT NULL,
                reason TEXT,
                updated_at TEXT NOT NULL
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

    def get_plan(self, chat_id: str) -> Plan | None:
        row = self.conn.execute(
            """
            SELECT chat_id, plan, status, reason, updated_at
            FROM plans
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()
        if row is None:
            return None

        return Plan(
            plan=row[1],
            status=row[2],
            reason=row[3],
            chat_id=row[0],
            updated_at=datetime.fromisoformat(row[4]),
        )

    # Hide until needed. Coud potentially offset stored state
    # def set_plan(self, plan: Plan) -> None:
    #     self._upsert_plan(plan)
    #     self.conn.commit()

    def save_processing_results(
        self,
        plans: list[Plan],
        last_processed_message_id: int,
    ) -> None:
        """Atomically save all chat results and advance the global cursor."""
        with self.conn:
            for plan in plans:
                self._upsert_plan(plan)
            self.conn.execute(
                """
                INSERT INTO agent_state (id, last_processed_message_id)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_processed_message_id = excluded.last_processed_message_id
                """,
                (last_processed_message_id,),
            )

    def _upsert_plan(self, plan: Plan) -> None:
        if (
            plan.chat_id is None
            or plan.updated_at is None
        ):
            raise ValueError("A stored plan requires chat and extraction metadata.")
        self.conn.execute(
            """
            INSERT INTO plans (
                chat_id, plan, status, reason, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                plan = excluded.plan,
                status = excluded.status,
                reason = excluded.reason,
                updated_at = excluded.updated_at
            """,
            (
                plan.chat_id,
                plan.plan,
                plan.status,
                plan.reason,
                plan.updated_at.astimezone(timezone.utc).isoformat(),
            ),
        )

    def close(self) -> None:
        self.conn.close()
