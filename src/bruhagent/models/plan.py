from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

PlanStatus = Literal["active", "stuck", "completed", "none"]

@dataclass(slots=True)
class PlanExtraction(BaseModel):
    """dataclass for info the be extracted from conversation"""
    status: PlanStatus
    plan: str | None
    reason: str
    confidence: float = 0.0

@dataclass(slots=True)
class Plan:
    """The latest planning state extracted from one conversation."""

    status: PlanStatus
    plan: str | None
    reason: str
    chat_id: str
    confidence: float = 0.0
    updated_at: datetime | None = None

    @classmethod
    def from_plan_extraction(
        cls,
        plan_extraction: PlanExtraction,
        chat_id: str,
        updated_at: datetime
    ) -> "Plan":
        return cls(
            status=plan_extraction.status,
            plan=plan_extraction.plan,
            reason=plan_extraction.reason,
            confidence=plan_extraction.confidence,
            chat_id=chat_id,
            updated_at=updated_at
        ) 
