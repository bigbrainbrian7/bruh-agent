import importlib.util
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from bruhagent.database import ChatDBReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    script_path = PROJECT_ROOT / "scripts" / "create_test_db.py"
    spec = importlib.util.spec_from_file_location("create_test_db", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.build_fake_db


class RecentMessagesTests(unittest.TestCase):
    def test_recent_messages_keeps_latest_thirty_from_last_week(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "interleaved_chat.db"
            load_builder()(
                PROJECT_ROOT / "data" / "interleaved_conversations.json",
                db_path,
            )
            reader = ChatDBReader(db_path)
            self.addCleanup(reader.close)

            messages = reader.get_messages(chat_id="fake-chat-context-window")
            first_new_message = next(
                message for message in messages if message.text.startswith("NEW-01")
            )
            history = reader.get_recent_messages(
                chat_id="fake-chat-context-window",
                before_message_id=first_new_message.id,
                after_timestamp=first_new_message.timestamp - timedelta(days=7),
            )

            self.assertEqual(len(history), 30)
            self.assertEqual(history[0].text, "RECENT-02")
            self.assertEqual(history[-1].text, "RECENT-31")
            self.assertTrue(all("OLD-" not in message.text for message in history))
            self.assertEqual(
                [message.id for message in history],
                sorted(message.id for message in history),
            )

            week_history = reader.get_recent_messages(
                chat_id="fake-chat-context-window",
                before_message_id=first_new_message.id,
                after_timestamp=first_new_message.timestamp - timedelta(days=7),
                limit=40,
            )
            self.assertEqual(len(week_history), 31)
            self.assertEqual(week_history[0].text, "RECENT-01")
            self.assertTrue(
                all("OLD-" not in message.text for message in week_history)
            )
