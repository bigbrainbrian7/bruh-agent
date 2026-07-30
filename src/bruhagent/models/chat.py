from dataclasses import dataclass

@dataclass(slots=True)
class Chat():
    chat_id: str
    last_processed_message_id: int
