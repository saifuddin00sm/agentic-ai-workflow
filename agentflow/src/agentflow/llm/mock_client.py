"""Mock LLM client for testing and offline demo."""

from __future__ import annotations

import json
import logging
from typing import Any

from agentflow.llm import LLMMessage, LLMResponse, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


class MockLLMClient:
    """Mock LLM client that returns scripted responses.

    Used for testing and offline demo mode. Responses are scripted
    as a sequence: each call to complete() pops the next response.
    """

    def __init__(
        self,
        responses: list[LLMResponse] | None = None,
        fixtures: dict[str, Any] | None = None,
    ) -> None:
        self._responses = list(responses or [])
        self._fixtures = fixtures or {}
        self._call_count = 0
        self._call_log: list[dict[str, Any]] = []

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def call_log(self) -> list[dict[str, Any]]:
        return self._call_log

    def add_response(self, response: LLMResponse) -> None:
        """Add a scripted response to the queue."""
        self._responses.append(response)

    def add_tool_call_response(
        self, tool_name: str, tool_input: dict[str, Any], tool_call_id: str = "toolu_mock_1"
    ) -> None:
        """Add a response that calls a tool."""
        self._responses.append(
            LLMResponse(
                content="",
                tool_calls=[
                    ToolCall(id=tool_call_id, name=tool_name, input=tool_input)
                ],
                stop_reason="tool_use",
            )
        )

    def add_text_response(self, text: str) -> None:
        """Add a simple text response."""
        self._responses.append(
            LLMResponse(content=text, stop_reason="end_turn")
        )

    async def complete(
        self,
        *,
        system: str,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Return the next scripted response."""
        self._call_count += 1
        self._call_log.append({
            "call_number": self._call_count,
            "system": system[:200],
            "message_count": len(messages),
            "tools": [t.name for t in tools] if tools else [],
        })

        if not self._responses:
            # Default fallback: return a generic response
            logger.warning("MockLLMClient: no more scripted responses, returning default")
            return LLMResponse(
                content='{"status": "mock_default"}',
                stop_reason="end_turn",
            )

        return self._responses.pop(0)

    def reset(self) -> None:
        """Reset the mock client state."""
        self._call_count = 0
        self._call_log.clear()
