"""Integration tests for the full pipeline."""

from __future__ import annotations

import pytest

from agentflow.llm import LLMResponse, ToolCall
from agentflow.llm.mock_client import MockLLMClient
from agentflow.models.events import EventType
from agentflow.pipeline import Pipeline


def create_happy_path_mock() -> MockLLMClient:
    """Create a mock client for the happy path scenario."""
    client = MockLLMClient()

    # Planner
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="plan_1",
            name="submit_result",
            input={
                "query": "Company due-diligence brief on TestCo",
                "company": "TestCo",
                "tasks": [
                    {"id": "task_1", "question": "What does TestCo do?", "suggested_tools": ["wikipedia"], "priority": 1},
                    {"id": "task_2", "question": "Financial overview?", "suggested_tools": ["stocks"], "priority": 1},
                ],
                "approach": "Basic due diligence.",
            },
        )],
        stop_reason="tool_use",
    ))

    # Researcher 1
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="res_1",
            name="submit_result",
            input={
                "task_id": "task_1",
                "question": "What does TestCo do?",
                "claims": [
                    {"text": "TestCo is a software company.", "source_url": "https://en.wikipedia.org/wiki/TestCo", "source_name": "Wikipedia", "confidence": 0.9, "evidence_id": "ev_1"},
                ],
                "summary": "TestCo is a software company.",
                "tool_calls_made": 1,
            },
        )],
        stop_reason="tool_use",
    ))

    # Researcher 2
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="res_2",
            name="submit_result",
            input={
                "task_id": "task_2",
                "question": "Financial overview?",
                "claims": [
                    {"text": "TestCo has $100M revenue.", "source_url": "https://finance.example.com/testco", "source_name": "Finance", "confidence": 0.8, "evidence_id": "ev_2"},
                ],
                "summary": "TestCo has $100M revenue.",
                "tool_calls_made": 1,
            },
        )],
        stop_reason="tool_use",
    ))

    # Analyst
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="analyst_1",
            name="submit_result",
            input={
                "key_insights": [
                    {"text": "TestCo is a growing software company.", "supporting_evidence": ["ev_1", "ev_2"], "confidence": 0.85},
                ],
                "risks": [],
                "open_questions": [],
                "evidence_refs": ["ev_1", "ev_2"],
                "degraded": False,
                "failed_tasks": [],
            },
        )],
        stop_reason="tool_use",
    ))

    # Writer
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="writer_1",
            name="submit_result",
            input={
                "title": "TestCo Due Diligence",
                "executive_summary": "TestCo is a software company with $100M revenue.",
                "sections": [
                    {"title": "Overview", "content": "TestCo is a software company [ev_1] with $100M revenue [ev_2].", "subsections": []},
                ],
                "citations": [
                    {"evidence_id": "ev_1", "source_url": "https://en.wikipedia.org/wiki/TestCo", "source_name": "Wikipedia", "claim_text": "Software company"},
                    {"evidence_id": "ev_2", "source_url": "https://finance.example.com/testco", "source_name": "Finance", "claim_text": "$100M revenue"},
                ],
                "degraded_coverage": False,
                "coverage_note": "",
            },
        )],
        stop_reason="tool_use",
    ))

    # Validator
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="val_1",
            name="submit_result",
            input={
                "passed": True,
                "issues": [],
                "score": 0.95,
                "summary": "Report passes all checks.",
            },
        )],
        stop_reason="tool_use",
    ))

    return client


class TestPipelineHappyPath:
    """Integration test: full happy path."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        mock = create_happy_path_mock()
        pipeline = Pipeline(llm=mock)

        events = []
        async for event in pipeline.run("Company due-diligence brief on TestCo"):
            events.append(event)

        # Should have run_completed
        completed = [e for e in events if e.type == EventType.RUN_COMPLETED]
        assert len(completed) == 1

        # Should not have run_failed
        failed = [e for e in events if e.type == EventType.RUN_FAILED]
        assert len(failed) == 0

    @pytest.mark.asyncio
    async def test_events_have_stages(self) -> None:
        mock = create_happy_path_mock()
        pipeline = Pipeline(llm=mock)

        events = []
        async for event in pipeline.run("Test"):
            events.append(event)

        stages_started = [e for e in events if e.type == EventType.STAGE_STARTED]
        stages_completed = [e for e in events if e.type == EventType.STAGE_COMPLETED]

        assert len(stages_started) >= 5  # planner, research, analyst, writer, validator
        assert len(stages_completed) >= 5


class TestPipelineAllFail:
    """Integration test: all research tasks fail."""

    @pytest.mark.asyncio
    async def test_all_research_fails(self) -> None:
        client = MockLLMClient()

        # Planner succeeds
        client.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="plan_1",
                name="submit_result",
                input={
                    "query": "Test query",
                    "company": "TestCo",
                    "tasks": [
                        {"id": "task_1", "question": "Q1?", "suggested_tools": ["wikipedia"], "priority": 1},
                    ],
                    "approach": "test",
                },
            )],
            stop_reason="tool_use",
        ))

        # All research fails (inject failure for wikipedia)
        pipeline = Pipeline(llm=client, inject_failures=["wikipedia"])

        events = []
        async for event in pipeline.run("Test query"):
            events.append(event)

        # Should have run_failed since all research failed
        failed = [e for e in events if e.type == EventType.RUN_FAILED]
        assert len(failed) >= 1


class TestPipelineDegradedMode:
    """Integration test: one tool failing but pipeline continues."""

    @pytest.mark.asyncio
    async def test_partial_failure(self) -> None:
        client = MockLLMClient()

        # Planner with 2 tasks
        client.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="plan_1",
                name="submit_result",
                input={
                    "query": "Test",
                    "company": "TestCo",
                    "tasks": [
                        {"id": "task_1", "question": "Q1?", "suggested_tools": ["wikipedia"], "priority": 1},
                        {"id": "task_2", "question": "Q2?", "suggested_tools": ["news"], "priority": 1},
                    ],
                    "approach": "test",
                },
            )],
            stop_reason="tool_use",
        ))

        # First researcher succeeds
        client.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="res_1",
                name="submit_result",
                input={
                    "task_id": "task_1",
                    "question": "Q1?",
                    "claims": [
                        {"text": "Fact.", "source_url": "https://example.com", "source_name": "Test", "confidence": 0.9, "evidence_id": "ev_1"},
                    ],
                    "summary": "Summary.",
                    "tool_calls_made": 1,
                },
            )],
            stop_reason="tool_use",
        ))

        # Second researcher fails (news is injected)
        # (no response needed - it'll fail before calling LLM)

        # Analyst
        client.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="analyst_1",
                name="submit_result",
                input={
                    "key_insights": [{"text": "Insight.", "supporting_evidence": ["ev_1"], "confidence": 0.8}],
                    "risks": [],
                    "open_questions": ["Q2 unanswered"],
                    "evidence_refs": ["ev_1"],
                    "degraded": True,
                    "failed_tasks": ["task_2"],
                },
            )],
            stop_reason="tool_use",
        ))

        # Writer
        client.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="writer_1",
                name="submit_result",
                input={
                    "title": "Report (Partial)",
                    "executive_summary": "Partial report.",
                    "sections": [{"title": "S1", "content": "Content [ev_1].", "subsections": []}],
                    "citations": [{"evidence_id": "ev_1", "source_url": "https://example.com", "source_name": "Test", "claim_text": "Fact"}],
                    "degraded_coverage": True,
                    "coverage_note": "Task 2 failed.",
                },
            )],
            stop_reason="tool_use",
        ))

        # Validator
        client.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id="val_1",
                name="submit_result",
                input={
                    "passed": True,
                    "issues": [],
                    "score": 0.7,
                    "summary": "Passes with degraded coverage noted.",
                },
            )],
            stop_reason="tool_use",
        ))

        pipeline = Pipeline(llm=client, inject_failures=["news"])
        events = []
        async for event in pipeline.run("Test"):
            events.append(event)

        # Should have warnings about degradation
        warnings = [e for e in events if e.type == EventType.WARNING]
        assert len(warnings) >= 1

        # Should still complete
        completed = [e for e in events if e.type == EventType.RUN_COMPLETED]
        assert len(completed) == 1
