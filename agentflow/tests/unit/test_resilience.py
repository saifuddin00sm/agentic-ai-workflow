"""Tests for resilience utilities."""

from __future__ import annotations

import asyncio

import pytest

from agentflow.resilience import (
    PipelineError,
    StageError,
    StageOutputError,
    ToolExecutionError,
    TransientError,
    retry,
    with_timeout,
)


class TestRetry:
    """Tests for the retry decorator."""

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self) -> None:
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        async def succeeds() -> str:
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeeds()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_transient(self) -> None:
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01, retry_on=(TransientError,))
        async def fails_then_succeeds() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError("transient")
            return "ok"

        result = await fails_then_succeeds()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_transient(self) -> None:
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01, retry_on=(TransientError,))
        async def permanent_error() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            await permanent_error()
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_exhausts_retries(self) -> None:
        call_count = 0

        @retry(max_attempts=2, base_delay=0.01, retry_on=(TransientError,))
        async def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise TransientError("always fails")

        with pytest.raises(TransientError):
            await always_fails()
        assert call_count == 2


class TestWithTimeout:
    """Tests for the timeout utility."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self) -> None:
        async def fast() -> str:
            return "done"

        result = await with_timeout(fast(), timeout_s=5.0, stage_name="test")
        assert result == "done"

    @pytest.mark.asyncio
    async def test_times_out(self) -> None:
        async def slow() -> str:
            await asyncio.sleep(10)
            return "done"

        with pytest.raises(StageError, match="Timed out"):
            await with_timeout(slow(), timeout_s=0.1, stage_name="slow_stage")


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_hierarchy(self) -> None:
        assert issubclass(StageError, PipelineError)
        assert issubclass(StageOutputError, StageError)
        assert issubclass(ToolExecutionError, PipelineError)
        assert issubclass(TransientError, PipelineError)

    def test_stage_error_message(self) -> None:
        err = StageError("planner", "failed to parse")
        assert "[planner]" in str(err)
        assert err.stage == "planner"

    def test_tool_error_message(self) -> None:
        err = ToolExecutionError("wikipedia", "timeout")
        assert "[tool:wikipedia]" in str(err)
        assert err.tool_name == "wikipedia"
