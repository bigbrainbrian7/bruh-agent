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
        analyzer: PlanAnalyzer,
    ):
        self.reader = reader
        self.state_store = state_store
        self.analyzer = analyzer

    def process_new_messages(
        self,
        since: datetime,
        through_message_id: int | None = None,
    ) -> dict[str, Plan]:
        chats = self.state_store.get_tracked_chats()
        print(f'Processing new messages after {since.strftime("%B %d, %Y - %H:%M")}')

        messages_by_chat: dict[str, list[Message]] = {}

        for chat in chats:
            new_messages = self.reader.get_messages(
                chat_id=chat.chat_id,
                after_message_id=chat.last_processed_message_id,
                after_timestamp=since
            )
            if not new_messages: 
                continue
            messages_by_chat[chat.chat_id] = new_messages
            # #for testing
            # if through_message_id is not None:
            #     new_messages = [
            #         message
            #         for message in new_messages
            #         if message.id <= through_message_id
            #     ]
            chat.last_processed_message_id = new_messages[-1].id

        processed_at = datetime.now(timezone.utc)
        plans: list[Plan] = []
        analyses: dict[str, Plan] = {}

        for chat_id, chat_messages in messages_by_chat.items():
            print(f"Processing chat {chat_id}")
            previous_plan = self.state_store.get_plan(chat_id)
            first_new_message = chat_messages[0]
            previous_messages = self.reader.get_messages(
                chat_id,
                before_message_id=first_new_message.id,
                after_timestamp=first_new_message.timestamp - timedelta(days=3),
                limit=30
            )
            plan_extraction = self.analyzer.analyze_chat(
                messages=chat_messages,
                previous_messages=previous_messages,
                previous_plan=previous_plan,
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
            chats=chats
        )
        return analyses
