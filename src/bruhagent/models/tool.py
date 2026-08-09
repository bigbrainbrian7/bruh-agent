from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ToolName = Literal["create_calendar_event"]


class CalendarEventArguments(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None
    notes: str | None = None


class ToolCall(BaseModel):
    """A proposed native action. The app validates and approves it before execution."""

    id: str
    name: ToolName
    arguments: CalendarEventArguments


class ToolResult(BaseModel):
    tool_call_id: str
    status: Literal["completed", "dismissed", "failed"]
    external_id: str | None = None
    summary: str
