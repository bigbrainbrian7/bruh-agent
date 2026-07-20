import json
import sqlite3
import time
from pathlib import Path

#TODO: add from_me feature (as well as adjust simulated json to reflect that)
def build_fake_db(json_path: str, db_path: str):
    json_path = Path(json_path)
    db_path = Path(db_path)

    with open(json_path) as f:
        conversations = json.load(f)

    # Start fresh each time
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE chat (
            ROWID INTEGER PRIMARY KEY,
            guid TEXT
        );
        CREATE TABLE handle (
            ROWID INTEGER PRIMARY KEY,
            id TEXT UNIQUE
        );
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY,
            text TEXT,
            date INTEGER,
            is_from_me INTEGER,
            handle_id INTEGER
        );
        CREATE TABLE chat_message_join (
            chat_id INTEGER,
            message_id INTEGER
        );
    """)

    handle_ids: dict[str, int] = {}  # sender name -> handle ROWID
    next_handle_id = 1
    next_message_id = 1
    base_time = int(time.time())  # fake starting timestamp

    for convo in conversations:
        chat_row_id = convo["id"]
        chat_guid = f"fake-chat-{chat_row_id}"

        conn.execute(
            "INSERT INTO chat (ROWID, guid) VALUES (?, ?)",
            (chat_row_id, chat_guid),
        )

        for i, msg in enumerate(convo["messages"]):
            sender = msg["sender"]

            # Resolve or create the handle for this sender
            if sender not in handle_ids:
                handle_ids[sender] = next_handle_id
                conn.execute(
                    "INSERT INTO handle (ROWID, id) VALUES (?, ?)",
                    (next_handle_id, sender),
                )
                next_handle_id += 1

            handle_id = handle_ids[sender]

            # Fake but ordered timestamps (10s apart), all treated as
            # not-from-me since every message has a named sender
            msg_date = base_time + (chat_row_id * 1000) + (i * 10)

            conn.execute(
                """INSERT INTO message
                   (ROWID, text, date, is_from_me, handle_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (next_message_id, msg["text"], msg_date, 0, handle_id),
            )
            conn.execute(
                "INSERT INTO chat_message_join (chat_id, message_id) VALUES (?, ?)",
                (chat_row_id, next_message_id),
            )
            next_message_id += 1

    conn.commit()
    conn.close()
    print(f"Built fake db at {db_path} with {len(conversations)} conversations "
          f"and {next_message_id - 1} messages ({len(handle_ids)} unique senders).")


if __name__ == "__main__":
    build_fake_db(
        json_path="../data/fake_conversations.json",
        db_path="../data/fake_chat.db",
    )