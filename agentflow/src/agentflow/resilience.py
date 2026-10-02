"""Resilience utilities: retry, timeouts, exception hierarchy."""

from __future__ import annotations

import asyncio
import functools
import logging
import random
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


# ── Exception hierarchy ──────────────────────────────────────────────────────


class PipelineError(Exception):
    """Base exception for all pipeline errors."""

    pass


class StageError(PipelineError):
    """Error during a pipeline stage."""

    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        super().__init__(f"[{stage}] {message}")


class StageOutputError(StageError):
    """Stage produced invalid output."""

    pass


class ToolExecutionError(PipelineError):
    """Error executing a tool."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"[tool:{tool_name}] {message}")


class LLMProviderError(PipelineError):
    """Error from the LLM provider."""

    pass


class TransientError(PipelineError):
    """A transient error that may succeed on retry."""

    pass


# ── Retry decorator ──────────────────────────────────────────────────────────


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: tuple[type[Exception], ...] = (TransientError, asyncio.TimeoutError),
) -> Callable[[F], F]:
    """Retry with exponential backoff + jitter.

    Only retries on specified transient error types.
    Never retries validation/4xx errors.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_error = e
                    if attempt == max_attempts:
                        logger.warning(
                            "Retry exhausted after %d attempts: %s",
                            max_attempts,
                            str(e),
                        )
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    wait = delay + jitter
                    logger.info(
                        "Attempt %d/%d failed (%s), retrying in %.1fs",
                        attempt,
                        max_attempts,
                        type(e).__name__,
                        wait,
                    )
                    await asyncio.sleep(wait)
                except Exception:
                    # Non-transient errors: don't retry
                    raise
            # Should never reach here, but satisfy type checker
            raise last_error or PipelineError("Retry failed")

        return wrapper  # type: ignore[return-value]

    return decorator


# ── Timeout utility ──────────────────────────────────────────────────────────


async def with_timeout(coro: Any, timeout_s: float, stage_name: str = "") -> Any:
    """Run a coroutine with a timeout, raising StageError on timeout."""
    try:
        async with asyncio.timeout(timeout_s):
            return await coro
    except TimeoutError:
        raise StageError(
            stage_name or "unknown",
            f"Timed out after {timeout_s}s",
        )
