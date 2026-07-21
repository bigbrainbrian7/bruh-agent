import sqlite3
from datetime import datetime

from ..models import Message

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

        params = []

        if after_message_id is not None:
            query += " WHERE chat.guid = ?"
            params.append(str(chat_id))

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

