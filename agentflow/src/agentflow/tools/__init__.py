"""Tool base class and shared HTTP helper."""

from __future__ import annotations

import logging
import time
from typing import Any, Generic, TypeVar

import httpx
from pydantic import BaseModel

from agentflow.resilience import ToolExecutionError, TransientError, retry

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Shared HTTP client with descriptive User-Agent (required by SEC EDGAR)
_http_client: httpx.AsyncClient | None = None

USER_AGENT = "AgentFlow/0.1 (research-bot; contact@example.com)"


def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared async HTTP client."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
    return _http_client


async def close_http_client() -> None:
    """Close the shared HTTP client."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


class ToolResult(BaseModel):
    """Standard tool result."""

    content: str
    is_error: bool = False
    metadata: dict[str, Any] = {}


class Tool(Generic[T]):
    """Base class for all tools.

    Subclasses define:
    - name: tool name
    - description: what the tool does (shown to LLM)
    - input_model: Pydantic model for input validation
    - run(): async implementation
    """

    name: str = ""
    description: str = ""
    input_model: type[T]  # type: ignore[assignment]
    max_output_chars: int = 4000

    def get_schema(self) -> dict[str, Any]:
        """Get JSON schema for the tool's input model."""
        return self.input_model.model_json_schema()

    def get_tool_definition(self) -> dict[str, Any]:
        """Get tool definition in the format expected by the LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_schema(),
        }

    async def execute(self, raw_input: dict[str, Any]) -> ToolResult:
        """Execute the tool with validated input.

        Validates input, runs the tool, truncates output.
        Catches all exceptions and returns structured error.
        """
        start = time.monotonic()
        try:
            # Validate input
            validated = self.input_model.model_validate(raw_input)
            # Run tool
            result = await self.run(validated)
            # Truncate output
            if len(result.content) > self.max_output_chars:
                result.content = result.content[:self.max_output_chars] + "\n...[truncated]"
            elapsed = int((time.monotonic() - start) * 1000)
            result.metadata["latency_ms"] = elapsed
            logger.info("Tool %s completed in %dms", self.name, elapsed)
            return result
        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            logger.warning("Tool %s failed after %dms: %s", self.name, elapsed, e)
            return ToolResult(
                content=f"Error: {type(e).__name__}: {str(e)[:500]}",
                is_error=True,
                metadata={"latency_ms": elapsed, "error_type": type(e).__name__},
            )

    async def run(self, input: T) -> ToolResult:  # noqa: A002
        """Implement this in subclasses."""
        raise NotImplementedError


async def http_get(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Shared HTTP GET with retry on transient errors."""
    client = get_http_client()

    @retry(max_attempts=2, base_delay=1.0)
    async def _get() -> httpx.Response:
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code == 429 or resp.status_code >= 500:
            raise TransientError(f"HTTP {resp.status_code}")
        return resp

    return await _get()
