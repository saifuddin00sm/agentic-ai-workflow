"""Anthropic Claude implementation of LLMClient."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from agentflow.config import get_settings
from agentflow.llm import LLMMessage, LLMResponse, ToolCall, ToolDefinition
from agentflow.resilience import LLMProviderError, TransientError, retry

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Anthropic Claude client implementing LLMClient protocol."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.anthropic_model

        if not self._api_key:
            raise LLMProviderError("ANTHROPIC_API_KEY not set")

        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    def _format_tools(
        self, tools: list[ToolDefinition] | None
    ) -> list[dict[str, Any]]:
        """Convert tool definitions to Anthropic format."""
        if not tools:
            return []
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ]

    def _format_messages(
        self, messages: list[LLMMessage]
    ) -> list[dict[str, Any]]:
        """Convert messages to Anthropic format."""
        result: list[dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg.content, str):
                result.append({"role": msg.role, "content": msg.content})
            else:
                # Already in structured format (tool results, etc.)
                result.append({"role": msg.role, "content": msg.content})
        return result

    @retry(max_attempts=3, base_delay=2.0)
    async def complete(
        self,
        *,
        system: str,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send completion to Anthropic Claude."""
        try:
            kwargs: dict[str, Any] = {
                "model": self._model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": self._format_messages(messages),
            }
            if tools:
                kwargs["tools"] = self._format_tools(tools)

            response = await self._client.messages.create(**kwargs)

            # Parse response
            text_parts: list[str] = []
            tool_calls: list[ToolCall] = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            input=block.input if isinstance(block.input, dict) else json.loads(block.input),
                        )
                    )

            token_usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

            return LLMResponse(
                content="\n".join(text_parts),
                tool_calls=tool_calls,
                stop_reason=response.stop_reason or "",
                token_usage=token_usage,
            )

        except anthropic.RateLimitError as e:
            raise TransientError(f"Rate limited: {e}") from e
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                raise TransientError(f"Server error {e.status_code}: {e}") from e
            raise LLMProviderError(f"API error {e.status_code}: {e}") from e
        except anthropic.APIConnectionError as e:
            raise TransientError(f"Connection error: {e}") from e
        except Exception as e:
            raise LLMProviderError(f"Unexpected error: {e}") from e
