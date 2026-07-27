from dataclasses import dataclass
from datetime import datetime
from typing import Literal


PlanStatus = Literal["active", "stuck", "completed", "none"]


@dataclass(slots=True)
class Plan:
    """The latest planning state extracted from one conversation."""

    has_plan: bool
    plan: str | None
    status: PlanStatus
    reason: str | None
    confidence: float = 0.0
    chat_id: str | None = None
    updated_at: datetime | None = None
