import argparse

from pathlib import Path
from bruhagent.analysis.message_processor import MessageProcessor
from bruhagent.database import ChatDBReader, StateStore


def main() -> None:

    DEFAULT_CHAT_DB = Path.home() / "Library" / "Messages" / "chat.db"

    DEFAULT_STATE_DB = (
        Path.home()
        / "Library"
        / "Application Support"
        / "Bruh Agent"
        / "state.db"
    )

    parser = argparse.ArgumentParser(prog="bruh")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("--chat-db", default=DEFAULT_CHAT_DB)
    scan_parser.add_argument("--state-db", default=DEFAULT_STATE_DB)
    scan_parser.add_argument("--model", default="qwen3:8b")

    args = parser.parse_args()

    if args.command == "scan":
        reader = ChatDBReader(args.chat_db)
        state_store = StateStore(args.state_db)

        try:
            processor = MessageProcessor(reader, state_store, model=args.model)
            plans = processor.process_new_messages()

            for chat_id, plan in plans.items():
                print(f"{chat_id}: {plan.status} — {plan.plan}")
        finally:
            reader.close()
            state_store.close()