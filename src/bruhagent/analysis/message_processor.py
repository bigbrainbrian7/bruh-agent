from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from bruhagent.database import ChatDBReader, StateStore
from bruhagent.models import Message, Plan

from .plan_analyzer import PlanAnalyzer


class MessageProcessor:
    """Run incremental message analysis with one global source checkpoint."""

    def __init__(
        self,
        reader: ChatDBReader,
        state_store: StateStore,
        model: str = "qwen3:8b",
    ):
        self.reader = reader
        self.state_store = state_store
        self.model = model

    def process_new_messages(
        self,
        since: datetime,
        through_message_id: int | None = None,
    ) -> dict[str, Plan]:
        cursor = self.state_store.get_last_processed_message_id()
        print(f'Processing new messages after {since.strftime("%B %d, %Y - %H:%M")}')

        new_messages = self.reader.get_messages(
            after_message_id=cursor,
            after_timestamp=since
        )
        if through_message_id is not None:
            new_messages = [
                message
                for message in new_messages
                if message.id <= through_message_id
            ]
        if not new_messages:
            return {}

        messages_by_chat: dict[str, list[Message]] = defaultdict(list)
        for message in new_messages:
            messages_by_chat[message.chat_id].append(message)

        processed_at = datetime.now(timezone.utc)
        plans: list[Plan] = []
        analyses: dict[str, Plan] = {}

        for chat_id, chat_messages in messages_by_chat.items():
            print(f"Processing chat {chat_id}")
            previous_plan = self.state_store.get_plan(chat_id)
            first_new_message = chat_messages[0]
            previous_messages = self.reader.get_recent_messages(
                chat_id,
                before_message_id=first_new_message.id,
                after_timestamp=first_new_message.timestamp - timedelta(days=3),
            )
            plan_extraction = PlanAnalyzer.analyze_chat(
                chat_messages,
                previous_messages=previous_messages,
                previous_plan=previous_plan,
                model=self.model,
            )
            plan = Plan.from_plan_extraction(
                plan_extraction=plan_extraction, 
                chat_id=chat_id, 
                updated_at=processed_at
            )
            analyses[chat_id] = plan
            plans.append(plan)

        self.state_store.save_processing_results(
            plans=plans,
            last_processed_message_id=new_messages[-1].id,
        )
        return analyses
