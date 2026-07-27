import sqlite3
from datetime import datetime, timedelta, timezone

from ..models import Message


APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


class ChatDBReader:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_messages(
        self,
        chat_id: str | None = None,
        after_message_id: int | None = None,
    ) -> list[Message]:

        query = """
        SELECT
            message.ROWID,
            chat.guid,
            handle.id,
            message.date,
            message.text,
            message.is_from_me
        FROM message
        JOIN chat_message_join
            ON message.ROWID = chat_message_join.message_id
        JOIN chat
            ON chat.ROWID = chat_message_join.chat_id
        LEFT JOIN handle
            ON handle.ROWID = message.handle_id
        """

        conditions = []
        params: list[str | int] = []

        if chat_id is not None:
            conditions.append("chat.guid = ?")
            params.append(str(chat_id))

        if after_message_id is not None:
            conditions.append("message.ROWID > ?")
            params.append(after_message_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY message.ROWID"

        rows = self.conn.execute(query, params).fetchall()

        return [self._row_to_message(row) for row in rows]

    def get_recent_messages(
        self,
        chat_id: str,
        before_message_id: int,
        after_timestamp: datetime | None = None,
        limit: int = 30,
    ) -> list[Message]:
        """Return preceding messages within the requested bounded window in chronological order."""
        if limit <= 0:
            return []

        query = """
        SELECT
            message.ROWID,
            chat.guid,
            handle.id,
            message.date,
            message.text,
            message.is_from_me
        FROM message
        JOIN chat_message_join
            ON message.ROWID = chat_message_join.message_id
        JOIN chat
            ON chat.ROWID = chat_message_join.chat_id
        LEFT JOIN handle
            ON handle.ROWID = message.handle_id
        WHERE chat.guid = ? AND message.ROWID < ?
        ORDER BY message.ROWID DESC
        LIMIT ?
        """
        rows = self.conn.execute(
            query,
            (chat_id, before_message_id, limit),
        ).fetchall()
        messages = [self._row_to_message(row) for row in reversed(rows)]
        if after_timestamp is not None:
            messages = [
                message
                for message in messages
                if message.timestamp >= after_timestamp
            ]
        return messages

    @staticmethod
    def _from_apple_timestamp(value: int | float) -> datetime:
        """Convert Apple's 2001-epoch seconds or nanoseconds to UTC."""
        seconds = value / 1_000_000_000 if abs(value) >= 1_000_000_000_000 else value
        return APPLE_EPOCH + timedelta(seconds=seconds)

    # TOOD: recognize when sender is self
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        return Message(
            id=row[0],
            chat_id=row[1],
            sender=row[2] if row[2] else "Me",
            timestamp=self._from_apple_timestamp(row[3]),
            text=row[4] or "",
            is_from_me=bool(row[5]),
        )
    
    def get_chat_guids(self, after_message_id: int | None = None) -> list[str]:
        query = """
        SELECT chat.guid
        FROM chat
        JOIN chat_message_join
            ON chat.ROWID = chat_message_join.chat_id
        JOIN message
            ON message.ROWID = chat_message_join.message_id
        """
        params = []

        if after_message_id is not None:
            query += " WHERE message.ROWID > ?"
            params.append(after_message_id)

        query += " GROUP BY chat.guid ORDER BY MIN(message.ROWID)"

        rows = self.conn.execute(query, params).fetchall()

        return [row[0] for row in rows]
    
    def close(self) -> None:
        self.conn.close()
