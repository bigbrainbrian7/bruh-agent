from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class Plan:
    """The planning state extracted from a group conversation."""

    has_plan: bool
    plan: str | None
    status: Literal["active", "stuck", "completed", "none"]
    reason: str | None
    confidence: float = 0.0
