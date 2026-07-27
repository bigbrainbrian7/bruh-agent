import argparse
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path


APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc).timestamp()


def build_fake_db(json_path: str | Path, db_path: str | Path) -> None:
    """Build a chat.db-shaped fixture from interleaved conversation JSON."""
    json_path = Path(json_path)
    db_path = Path(db_path)

    with json_path.open() as fixture_file:
        conversations = json.load(fixture_file)

    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE chat (
            ROWID INTEGER PRIMARY KEY,
            guid TEXT NOT NULL UNIQUE
        );
        CREATE TABLE handle (
            ROWID INTEGER PRIMARY KEY,
            id TEXT NOT NULL UNIQUE
        );
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY,
            text TEXT,
            date INTEGER NOT NULL,
            is_from_me INTEGER NOT NULL,
            handle_id INTEGER
        );
        CREATE TABLE chat_message_join (
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL
        );
        """
    )

    chat_rows: dict[str, int] = {}
    events = []
    for chat_row_id, conversation in enumerate(conversations, start=1):
        conversation_id = str(conversation["id"])
        chat_rows[conversation_id] = chat_row_id
        conn.execute(
            "INSERT INTO chat (ROWID, guid) VALUES (?, ?)",
            (chat_row_id, f"fake-chat-{conversation_id}"),
        )

        for message_number, message in enumerate(conversation["messages"], start=1):
            events.append(
                (
                    message.get("offset_minutes", chat_row_id * 10_000 + message_number),
                    chat_row_id,
                    message_number,
                    conversation_id,
                    message,
                )
            )

    events.sort(key=lambda event: event[:3])
    handle_ids: dict[str, int] = {}
    next_handle_id = 1
    base_time_ns = int((time.time() - APPLE_EPOCH) * 1_000_000_000)

    for message_id, (offset_minutes, _, _, conversation_id, message) in enumerate(
        events,
        start=1,
    ):
        sender = message["sender"]
        is_from_me = bool(message.get("is_from_me", False))
        handle_id = None
        if not is_from_me:
            if sender not in handle_ids:
                handle_ids[sender] = next_handle_id
                conn.execute(
                    "INSERT INTO handle (ROWID, id) VALUES (?, ?)",
                    (next_handle_id, sender),
                )
                next_handle_id += 1
            handle_id = handle_ids[sender]

        conn.execute(
            """
            INSERT INTO message (ROWID, text, date, is_from_me, handle_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message_id,
                message["text"],
                base_time_ns + offset_minutes * 60 * 1_000_000_000,
                is_from_me,
                handle_id,
            ),
        )
        conn.execute(
            "INSERT INTO chat_message_join (chat_id, message_id) VALUES (?, ?)",
            (chat_rows[conversation_id], message_id),
        )

    conn.commit()
    conn.close()
    print(
        f"Built {db_path} from {json_path}: {len(conversations)} chats and "
        f"{len(events)} interleaved messages."
    )


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Build a chat.db-shaped fixture from conversation JSON.",
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        type=Path,
        default=project_root / "data/interleaved_conversations.json",
    )
    parser.add_argument(
        "db_path",
        nargs="?",
        type=Path,
        default=project_root / "data/interleaved_chat.db",
    )
    args = parser.parse_args()
    build_fake_db(args.json_path, args.db_path)


if __name__ == "__main__":
    main()
