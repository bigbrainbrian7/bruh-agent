import argparse
import json
import sqlite3
import sys
from contextlib import nullcontext, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import fill

from bruhagent.analysis.message_processor import MessageProcessor
from bruhagent.analysis.plan_analyzer import PlanAnalyzer
from bruhagent.database import ChatDBReader, StateStore
from bruhagent.llm import (
    LLMError,
    ProviderAuthenticationError,
    ProviderResponseError,
    ProviderUnavailableError,
    create_provider,
)


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
    scan_parser.add_argument(
        "--provider",
        choices=["ollama", "gemini"],
        default="ollama",
        help="Language-model provider (default: ollama)",
    )
    scan_parser.add_argument(
        "--model",
        help="Model name; defaults to qwen3:1.7b for Ollama, gemini-3.5-flash-lite for Gemini",
    )
    # TODO: Determine good time frame to process new messages if haven't processed in a while
    # essentially jsut the default since-hours value
    scan_parser.add_argument(
        "--since-hours",
        type=positive_int,
        default=12,
        help="Initial scan window; ignored after the first successful scan (default: 12)",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print scan results as JSON",
    )

    chats_parser = subparsers.add_parser("chats", help="Manage tracked chats")
    chats_subparsers = chats_parser.add_subparsers(
        dest="chats_command",
        required=True
    )
    list_parser = chats_subparsers.add_parser(
        "list",
        help="List chats available in Messages",
    )
    list_parser.add_argument(
        "--limit",
        type=positive_int,
        default=10,
        help="Show only this many most recently active chats",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Print chats as JSON",
    )

    tracked_parser = chats_subparsers.add_parser(
        "tracked",
        help="List chats that are analyzed when you scan",
    )
    tracked_parser.add_argument(
        "--json",
        action="store_true",
        help="Print tracked chats as JSON",
    )
    add_chat_parser = chats_subparsers.add_parser("add", help="Add a chat to be analyzed when you scan")
    add_chat_parser.add_argument("chat_id")

    remove_chat_parser = chats_subparsers.add_parser("rm", help="Remove a chat to be analyzed when you scan")
    remove_chat_parser.add_argument("chat_id")



    args = parser.parse_args()

    if args.command == "chats":
        state_store = None

        try:
            state_store = StateStore(DEFAULT_STATE_DB)

            if args.chats_command == "list":
                reader = None
                try:
                    reader = ChatDBReader(DEFAULT_CHAT_DB)
                    chat_ids = reader.get_chat_ids(limit=args.limit)
                    if args.json:
                        print(json.dumps({"chats": [{"chat_id": chat_id} for chat_id in chat_ids]}))
                    else:
                        print("most recent chat_ids")
                        for chat_id in chat_ids:
                            print(chat_id)
                finally:
                    if reader is not None:
                        reader.close()
            elif args.chats_command == "tracked":
                chats = state_store.get_tracked_chats()

                if args.json:
                    print(
                        json.dumps(
                            {
                                "chats": [
                                    {
                                        "chat_id": chat.chat_id,
                                        "last_processed_message_id": (
                                            chat.last_processed_message_id
                                        ),
                                    }
                                    for chat in chats
                                ]
                            }
                        )
                    )
                elif not chats:
                    print("No chats are being analyzed.")
                else:
                    for chat in chats:
                        print(chat.chat_id)

            elif args.chats_command == "add":
                state_store.add_tracked_chat(args.chat_id)
                print(f"Now analyzing: {args.chat_id}")

            elif args.chats_command == "rm":
                removed = state_store.remove_tracked_chat(args.chat_id)

                if removed:
                    print(f"Stopped analyzing: {args.chat_id}")
                else:
                    print(f"Chat was not being analyzed: {args.chat_id}")

            return 0

        except sqlite3.OperationalError as error:
                    print(f"Database error: {error}", file=sys.stderr)
                    return 1
        finally:
            if state_store is not None:
                state_store.close()

    if args.command == "scan":
        reader = None
        state_store = None

        try:
            reader = ChatDBReader(args.chat_db)
            state_store = StateStore(DEFAULT_STATE_DB)
            provider = create_provider(args.provider, args.model)
            analyzer = PlanAnalyzer(provider)
            processor = MessageProcessor(reader, state_store, analyzer=analyzer)
            since = datetime.now(timezone.utc) - timedelta(hours=args.since_hours)
            output = redirect_stdout(sys.stderr) if args.json else nullcontext()
            with output:
                plans = processor.process_new_messages(since=since)

            if args.json:
                print(
                    json.dumps(
                        {
                            "plans": [
                                {
                                    "chat_id": plan.chat_id,
                                    "status": plan.status,
                                    "plan": plan.plan,
                                    "blockers": plan.blockers,
                                    "reason": plan.reason,
                                    "updated_at": (
                                        plan.updated_at.isoformat()
                                        if plan.updated_at is not None
                                        else None
                                    ),
                                }
                                for plan in plans.values()
                            ]
                        }
                    )
                )
                return 0

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
        except ProviderAuthenticationError as error:
            print(error, file=sys.stderr)
            return 1
        except ProviderUnavailableError as error:
            print(error, file=sys.stderr)
            return 1
        except ProviderResponseError as error:
            print(error, file=sys.stderr)
            return 1
        except (LLMError, ValueError) as error:
            print(error, file=sys.stderr)
            return 1
        finally:
            if reader is not None:
                reader.close()
            if state_store is not None:
                state_store.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
