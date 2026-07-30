import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..models import Message


APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

BASE_QUERY = """
        SELECT
            message.ROWID,
            chat.guid,
            handle.id,
            message.date,
            message.text,
            message.is_from_me,
            message.attributedBody
        FROM message
        JOIN chat_message_join
            ON message.ROWID = chat_message_join.message_id
        JOIN chat
            ON chat.ROWID = chat_message_join.chat_id
        LEFT JOIN handle
            ON handle.ROWID = message.handle_id
        """


class ChatDBReader:

    def __init__(self, db_path: str | Path):
        path = Path(db_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Messages database not found: {path}")

        self.conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def get_messages(
        self,
        chat_id: str | None = None,
        after_message_id: int | None = None,
        before_message_id: int | None = None,
        after_timestamp: datetime | None = None,
        limit: int | None = None,
    ) -> list[Message]:

        query = BASE_QUERY

        conditions = []
        params: list[str | int] = []

        if chat_id is not None:
            conditions.append("chat.guid = ?")
            params.append(str(chat_id))

        if after_message_id is not None:
            conditions.append("message.ROWID > ?")
            params.append(after_message_id)

        if before_message_id is not None:
            conditions.append("message.ROWID < ?")
            params.append(before_message_id)

        if after_timestamp is not None:
            conditions.append("message.date > ?")
            params.append(self._to_apple_timestamp(after_timestamp))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)


        query += " ORDER BY message.ROWID DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.conn.execute(query, params).fetchall()

        return [self._row_to_message(row) for row in reversed(rows)]

    @staticmethod
    def _from_apple_timestamp(value: int | float) -> datetime:
        """Convert Apple's 2001-epoch seconds or nanoseconds to UTC."""
        seconds = value / 1_000_000_000 if abs(value) >= 1_000_000_000_000 else value
        return APPLE_EPOCH + timedelta(seconds=seconds)
    
    @staticmethod
    def _to_apple_timestamp(value: datetime) -> int:
        """Convert UTC to Apple's 2001-epoch nanoseconds."""
        datetime_apple_format = value - APPLE_EPOCH
        return int(datetime_apple_format.total_seconds() * 1_000_000_000)

    # TOOD: recognize when sender is self
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        id, chat_id, sender, timestamp, text, is_from_me, attributed_body = row

        # code taken from here 
        # github.com/my-other-github-account/imessage_tools/blob/master/imessage_tools.py

        is_from_me = bool(is_from_me)
        sender = sender if sender and not is_from_me else "Me"
        timestamp = self._from_apple_timestamp(timestamp)

        if text is not None:
            body = text
        # TODO: handle other media types (eg. video)
        elif attributed_body is None:
            body = ""
        else:
            attributed_body = attributed_body.decode('utf-8', errors='replace')

            if "NSNumber" in str(attributed_body):
                attributed_body = str(attributed_body).split("NSNumber")[0]
                if "NSString" in attributed_body:
                    attributed_body = str(attributed_body).split("NSString")[1]
                    if "NSDictionary" in attributed_body:
                        attributed_body = str(attributed_body).split("NSDictionary")[0]
                        attributed_body = attributed_body[6:-12]
                        body = attributed_body


        return Message(
            id=id,
            chat_id=chat_id,
            sender=sender,
            timestamp=timestamp,
            text=body,
        )
    
    def get_chat_ids(
            self, 
            after_message_id: int | None = None,
            limit: int | None = None,
        ) -> list[str]:
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

        query += " GROUP BY chat.guid ORDER BY MAX(message.ROWID) DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        

        return [row[0] for row in rows]
    
    def close(self) -> None:
        self.conn.close()
