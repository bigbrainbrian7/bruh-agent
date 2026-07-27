from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

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
        through_message_id: int | None = None,
    ) -> dict[str, Plan]:
        cursor = self.state_store.get_last_processed_message_id()
        new_messages = self.reader.get_messages(after_message_id=cursor)
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
            previous_plan = self.state_store.get_plan(chat_id)
            previous_messages = self.reader.get_recent_messages(chat_id, cursor)
            plan = PlanAnalyzer.analyze_chat(
                chat_messages,
                previous_messages=previous_messages,
                previous_plan=previous_plan,
                model=self.model,
            )
            analyses[chat_id] = plan
            plans.append(
                replace(
                    plan,
                    chat_id=chat_id,
                    updated_at=processed_at,
                )
            )

        self.state_store.save_processing_results(
            plans=plans,
            last_processed_message_id=new_messages[-1].id,
        )
        return analyses
