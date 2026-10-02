"""LLM client protocol and types."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Tool definition sent to the LLM."""

    name: str
    description: str
    input_schema: dict[str, Any] = Field(description="JSON Schema for tool input")


class ToolCall(BaseModel):
    """A tool call requested by the LLM."""

    id: str
    name: str
    input: dict[str, Any]


class ToolResult(BaseModel):
    """Result of executing a tool call."""

    tool_use_id: str
    content: str
    is_error: bool = False


class LLMMessage(BaseModel):
    """A message in the conversation."""

    role: str  # "user", "assistant", "system"
    content: str | list[dict[str, Any]] = ""


class LLMResponse(BaseModel):
    """Response from the LLM."""

    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    stop_reason: str = ""
    token_usage: dict[str, int] = Field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM providers."""

    async def complete(
        self,
        *,
        system: str,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a completion request to the LLM.

        Args:
            system: System prompt
            messages: Conversation messages
            tools: Available tool definitions
            max_tokens: Maximum tokens in response

        Returns:
            LLM response with content and/or tool calls
        """
        ...
