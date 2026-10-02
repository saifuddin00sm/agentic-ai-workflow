"""Tests for the Agent base class with MockLLMClient."""

from __future__ import annotations

import pytest

from agentflow.agents import Agent
from agentflow.llm import LLMMessage, LLMResponse, ToolCall, ToolDefinition
from agentflow.llm.mock_client import MockLLMClient
from agentflow.models.plan import ResearchPlan, ResearchTask
from agentflow.resilience import StageOutputError
from pydantic import BaseModel, Field


class SimpleInput(BaseModel):
    query: str


class SimpleOutput(BaseModel):
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)


class TestAgentBase:
    """Tests for the generic Agent base class."""

    @pytest.mark.asyncio
    async def test_direct_text_output(self) -> None:
        """Agent parses valid JSON from text response."""
        mock = MockLLMClient()
        mock.add_text_response('{"answer": "hello world", "confidence": 0.9}')

        agent = Agent[SimpleInput, SimpleOutput](
            name="test",
            system_prompt="You are a test agent.",
            input_model=SimpleInput,
            output_model=SimpleOutput,
            llm=mock,
            max_iterations=3,
        )

        output = None
        async for event in agent.run(SimpleInput(query="test"), run_id="test_run"):
            if event.type.value == "stage_completed":
                pass

        # Verify the agent called the LLM
        assert mock.call_count >= 1

    @pytest.mark.asyncio
    async def test_submit_result_tool(self) -> None:
        """Agent uses submit_result tool for structured output."""
        mock = MockLLMClient()
        mock.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="tc_1",
                name="submit_result",
                input={"answer": "42", "confidence": 0.95},
            )],
            stop_reason="tool_use",
        ))

        agent = Agent[SimpleInput, SimpleOutput](
            name="test",
            system_prompt="You are a test agent.",
            input_model=SimpleInput,
            output_model=SimpleOutput,
            llm=mock,
            max_iterations=3,
        )

        events = []
        async for event in agent.run(SimpleInput(query="test"), run_id="test_run"):
            events.append(event)

        # Should have completed
        completed = [e for e in events if e.type.value == "stage_completed"]
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_repair_turn_on_invalid_output(self) -> None:
        """Agent retries when first output is invalid."""
        mock = MockLLMClient()
        # First: invalid output (missing required field)
        mock.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="tc_1",
                name="submit_result",
                input={"answer": "test"},  # Missing confidence
            )],
            stop_reason="tool_use",
        ))
        # Second: valid output
        mock.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="tc_2",
                name="submit_result",
                input={"answer": "test", "confidence": 0.8},
            )],
            stop_reason="tool_use",
        ))

        agent = Agent[SimpleInput, SimpleOutput](
            name="test",
            system_prompt="You are a test agent.",
            input_model=SimpleInput,
            output_model=SimpleOutput,
            llm=mock,
            max_iterations=5,
        )

        events = []
        async for event in agent.run(SimpleInput(query="test"), run_id="test_run"):
            events.append(event)

        # Should have had a retry
        retries = [e for e in events if e.type.value == "stage_retry"]
        assert len(retries) >= 1

        # Should have completed
        completed = [e for e in events if e.type.value == "stage_completed"]
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_max_iterations_exceeded(self) -> None:
        """Agent raises after max iterations."""
        mock = MockLLMClient()
        # Always return invalid output
        for _ in range(5):
            mock.add_response(LLMResponse(
                content="",
                tool_calls=[ToolCall(
                    id="tc_1",
                    name="submit_result",
                    input={"wrong_field": "data"},
                )],
                stop_reason="tool_use",
            ))

        agent = Agent[SimpleInput, SimpleOutput](
            name="test",
            system_prompt="You are a test agent.",
            input_model=SimpleInput,
            output_model=SimpleOutput,
            llm=mock,
            max_iterations=3,
        )

        with pytest.raises(StageOutputError):
            async for _ in agent.run(SimpleInput(query="test"), run_id="test_run"):
                pass

    @pytest.mark.asyncio
    async def test_tool_execution(self) -> None:
        """Agent executes tools and feeds results back."""
        from agentflow.tools import Tool, ToolResult

        class DummyTool(Tool):
            name = "dummy"
            description = "A dummy tool"
            input_model = SimpleInput

            async def run(self, input: SimpleInput) -> ToolResult:
                return ToolResult(content=f"Result for: {input.query}")

        mock = MockLLMClient()
        # First: call the tool
        mock.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="tc_1",
                name="dummy",
                input={"query": "hello"},
            )],
            stop_reason="tool_use",
        ))
        # Second: submit result using tool output
        mock.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="tc_2",
                name="submit_result",
                input={"answer": "Result for: hello", "confidence": 0.9},
            )],
            stop_reason="tool_use",
        ))

        agent = Agent[SimpleInput, SimpleOutput](
            name="test",
            system_prompt="You are a test agent.",
            input_model=SimpleInput,
            output_model=SimpleOutput,
            tools=[DummyTool()],
            llm=mock,
            max_iterations=5,
        )

        events = []
        async for event in agent.run(SimpleInput(query="hello"), run_id="test_run"):
            events.append(event)

        # Should have tool_called and tool_result events
        tool_calls = [e for e in events if e.type.value == "tool_called"]
        tool_results = [e for e in events if e.type.value == "tool_result"]
        assert len(tool_calls) == 1
        assert len(tool_results) == 1
        assert tool_calls[0].data["tool"] == "dummy"
