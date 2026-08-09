from dataclasses import dataclass, field

@dataclass(slots=True)
class Chat():
    chat_id: str
    last_processed_message_id: int
    display_name: str | None = None
    participant_handles: list[str] = field(default_factory=list)
