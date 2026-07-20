import sqlite3
from datetime import datetime

from ..models import Message

class SQLiteReader:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_messages(
        self,
        chat_id: str,
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
        WHERE chat.guid = ?
        """

        params = [chat_id]

        if after_message_id is not None:
            query += " AND message.ROWID > ?"
            params.append(str(after_message_id))

        query += " ORDER BY message.ROWID"

        rows = self.conn.execute(query, params).fetchall()

        messages = []

        for row in rows:
            messages.append(
                Message(
                    id=row[0],
                    chat_id=row[1],
                    sender=row[2] if row[2] else "Me",
                    timestamp=datetime.fromtimestamp(row[3]),
                    text=row[4] or "",
                    is_from_me=bool(row[5]),
                )
            )

        return messages