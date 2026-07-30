from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Message:
    id: int
    chat_id: str
    sender: str
    timestamp: datetime
    text: str
    # is_from_me: bool