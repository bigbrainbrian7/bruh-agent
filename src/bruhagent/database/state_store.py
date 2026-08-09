import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..models import Chat, Plan, ToolCall


class StateStore:
    """Store Bruh Agent's global message-processing checkpoint."""

    def __init__(self, db_path: str | Path):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                chat_id TEXT PRIMARY KEY,
                plan TEXT,
                blockers TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL,
                reason TEXT,
                tool_calls TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tracked_chats (
                chat_id TEXT PRIMARY KEY,
                last_processed_message_id INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def get_plan(self, chat_id: str) -> Plan | None:
        row = self.conn.execute(
            """
            SELECT chat_id, plan, blockers, status, reason, tool_calls, updated_at
            FROM plans
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()
        if row is None:
            return None

        return Plan(
            plan=row[1],
            blockers=json.loads(row[2]),
            status=row[3],
            reason=row[4],
            chat_id=row[0],
            tool_calls=[ToolCall.model_validate(item) for item in json.loads(row[5])],
            updated_at=datetime.fromisoformat(row[6]),
        )

    # Hide until needed. Coud potentially offset stored state
    # def set_plan(self, plan: Plan) -> None:
    #     self._upsert_plan(plan)
    #     self.conn.commit()

    def save_processing_results(
        self,
        plans: list[Plan],
        chats: list[Chat],
    ) -> None:
        """Atomically save all chat results and advance the global cursor."""
        with self.conn:
            for plan in plans:
                self._upsert_plan(plan)
            for chat in chats:
                self._upsert_tracked_chat(chat)

    def _upsert_plan(self, plan: Plan) -> None:
        if (
            plan.chat_id is None
            or plan.updated_at is None
        ):
            raise ValueError("A stored plan requires chat and extraction metadata.")
        self.conn.execute(
            """
            INSERT INTO plans (
                chat_id, plan, blockers, status, reason, tool_calls, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                plan = excluded.plan,
                blockers = excluded.blockers,
                status = excluded.status,
                reason = excluded.reason,
                tool_calls = excluded.tool_calls,
                updated_at = excluded.updated_at
            """,
            (
                plan.chat_id,
                plan.plan,
                json.dumps(plan.blockers or []),
                plan.status,
                plan.reason,
                json.dumps([tool_call.model_dump(mode="json") for tool_call in plan.tool_calls]),
                plan.updated_at.astimezone(timezone.utc).isoformat(),
            ),
        )

    def get_tracked_chats(self) -> list[Chat]:
        rows = self.conn.execute("""
            SELECT chat_id, last_processed_message_id FROM tracked_chats
        """).fetchall()

        return [Chat(chat_id=row[0], last_processed_message_id=row[1]) for row in rows]

    def _upsert_tracked_chat(self, chat: Chat) -> None:
        self.conn.execute(
            """
            INSERT INTO tracked_chats (
                chat_id, last_processed_message_id
            ) VALUES (?, ?)
            ON CONFLICT (chat_id) DO UPDATE SET
                last_processed_message_id = excluded.last_processed_message_id
            """,
            (chat.chat_id, chat.last_processed_message_id)
        )

    def add_tracked_chat(self, chat_id: str) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO tracked_chats (chat_id)
                VALUES (?)
                ON CONFLICT(chat_id) DO NOTHING
                """,
                (chat_id,),
            )

        return cursor.rowcount == 1


    def remove_tracked_chat(self, chat_id: str) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                """
                DELETE FROM tracked_chats
                WHERE chat_id = ?
                """,
                (chat_id,),
            )

        return cursor.rowcount == 1

    def close(self) -> None:
        self.conn.close()
