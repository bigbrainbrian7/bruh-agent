import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import fill

from openai import APIConnectionError, APIStatusError

from bruhagent.analysis.message_processor import MessageProcessor
from bruhagent.database import ChatDBReader, StateStore


DEFAULT_CHAT_DB = Path.home() / "Library" / "Messages" / "chat.db"
DEFAULT_STATE_DB = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Bruh Agent"
    / "state.db"
)


def positive_int(value: str) -> int:
    integer = int(value)
    if integer <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return integer


def main() -> int:
    parser = argparse.ArgumentParser(prog="bruh")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Analyze new iMessage conversations")
    scan_parser.add_argument("--chat-db", type=Path, default=DEFAULT_CHAT_DB)
    scan_parser.add_argument("--state-db", type=Path, default=DEFAULT_STATE_DB)
    scan_parser.add_argument("--model", default="qwen3:8b")
    # TODO: Determine good time frame to process new messages if haven't processed in a while
    # essentially jsut the default since-hours value
    scan_parser.add_argument(
        "--since-hours",
        type=positive_int,
        default=12,
        help="Initial scan window; ignored after the first successful scan (default: 12)",
    )

    args = parser.parse_args()

    if args.command == "scan":
        reader = None
        state_store = None

        try:
            reader = ChatDBReader(args.chat_db)
            state_store = StateStore(args.state_db)
            processor = MessageProcessor(reader, state_store, model=args.model)
            since = datetime.now(timezone.utc) - timedelta(hours=args.since_hours)
            plans = processor.process_new_messages(since=since)

            if not plans:
                print("No new messages to analyze.")
            for chat_id, plan in plans.items():
                print("=" * 72)
                print(f"Chat: {chat_id}")
                print(f"Status: {plan.status.upper()}")
                print()
                print("Plan:")
                print(fill(plan.plan or "No plan identified.", width=72,
                           initial_indent="  ", subsequent_indent="  "))
                print()
                print("Blockers:")
                if plan.blockers:
                    for blocker in plan.blockers:
                        print(fill(blocker, width=72, initial_indent="  - ",
                                   subsequent_indent="    "))
                else:
                    print("  None")
                print()
                print("Reason:")
                print(fill(plan.reason, width=72, initial_indent="  ",
                           subsequent_indent="  "))
            if plans:
                print("=" * 72)
            return 0
        except FileNotFoundError as error:
            print(error, file=sys.stderr)
            return 1
        except PermissionError:
            print(
                "Cannot read the Messages database. Give your terminal Full Disk Access "
                "in System Settings, then try again.",
                file=sys.stderr,
            )
            return 1
        except sqlite3.OperationalError as error:
            print(f"Database error: {error}", file=sys.stderr)
            return 1
        except APIConnectionError:
            print(
                f"Cannot connect to Ollama at http://localhost:11434. "
                f"Start Ollama and ensure model '{args.model}' is installed.",
                file=sys.stderr,
            )
            return 1
        except APIStatusError as error:
            print(f"Ollama returned an API error: {error}", file=sys.stderr)
            return 1
        finally:
            if reader is not None:
                reader.close()
            if state_store is not None:
                state_store.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
