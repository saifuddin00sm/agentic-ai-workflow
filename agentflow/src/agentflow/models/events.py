"""Event models for the pipeline event stream."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of pipeline events."""

    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_RETRY = "stage_retry"
    STAGE_FAILED = "stage_failed"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    TOOL_FAILED = "tool_failed"
    WARNING = "warning"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class PipelineEvent(BaseModel):
    """A single event in the pipeline event stream."""

    type: EventType
    run_id: str
    stage: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = 0

    def summary(self) -> str:
        """Human-readable summary of the event."""
        match self.type:
            case EventType.STAGE_STARTED:
                return f"▶ Stage: {self.stage}"
            case EventType.STAGE_COMPLETED:
                return f"✓ Stage: {self.stage} ({self.latency_ms}ms)"
            case EventType.STAGE_FAILED:
                return f"✗ Stage failed: {self.stage}"
            case EventType.STAGE_RETRY:
                return f"↻ Stage retry: {self.stage}"
            case EventType.TOOL_CALLED:
                tool_name = self.data.get("tool", "?")
                return f"  🔧 {tool_name}({self.data.get('args', {})})"
            case EventType.TOOL_RESULT:
                tool_name = self.data.get("tool", "?")
                return f"  ✓ {tool_name} → {self.data.get('summary', '')[:60]}"
            case EventType.TOOL_FAILED:
                tool_name = self.data.get("tool", "?")
                return f"  ✗ {tool_name}: {self.data.get('error', '')[:60]}"
            case EventType.WARNING:
                return f"  ⚠ {self.data.get('message', '')}"
            case EventType.RUN_COMPLETED:
                return f"🏁 Run completed ({self.latency_ms}ms)"
            case EventType.RUN_FAILED:
                return f"💥 Run failed: {self.data.get('error', '')}"
        return str(self.type)
