from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from .tool import ToolCall

PlanStatus = Literal["active", "stuck", "completed", "none"]

@dataclass(slots=True)
class PlanExtraction(BaseModel):
    """dataclass for info the be extracted from conversation"""
    status: PlanStatus
    plan: str | None
    blockers: list[str] | None
    reason: str
    confidence: float = 0.0
    tool_calls: list[ToolCall] = Field(default_factory=list)

@dataclass(slots=True)
class Plan:
    """The latest planning state extracted from one conversation."""

    status: PlanStatus
    plan: str | None
    blockers: list[str] | None
    reason: str
    chat_id: str
    confidence: float = 0.0
    tool_calls: list[ToolCall] = field(default_factory=list)
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
            blockers=plan_extraction.blockers,
            reason=plan_extraction.reason,
            confidence=plan_extraction.confidence,
            tool_calls=plan_extraction.tool_calls,
            chat_id=chat_id,
            updated_at=updated_at
        ) 
