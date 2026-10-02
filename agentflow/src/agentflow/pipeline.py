"""Pipeline orchestrator - manages the full research workflow."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, AsyncIterator

from agentflow.agents.analyst import AnalystAgent, AnalystInput
from agentflow.agents.planner import PlannerAgent, PlannerInput
from agentflow.agents.researcher import ResearcherAgent, ResearcherInput
from agentflow.agents.validator import ValidatorAgent, ValidatorInput
from agentflow.agents.writer import WriterAgent, WriterInput
from agentflow.config import get_settings
from agentflow.llm import LLMClient, LLMMessage
from agentflow.models.analysis import Analysis
from agentflow.models.events import EventType, PipelineEvent
from agentflow.models.findings import ResearchFindings
from agentflow.models.plan import ResearchPlan, ResearchTask
from agentflow.models.report import FinalReport
from agentflow.models.validation import ValidationResult
from agentflow.resilience import PipelineError, StageError, with_timeout
from agentflow.tools import Tool
from agentflow.tools.registry import ToolRegistry, create_default_registry

logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline orchestrator.

    Runs the full research workflow:
    1. Plan → 2. Research (parallel) → 3. Analyze → 4. Write → 5. Validate
    With revision loop if validation fails.
    """

    def __init__(
        self,
        llm: LLMClient,
        tool_registry: ToolRegistry | None = None,
        inject_failures: list[str] | None = None,
    ) -> None:
        self.llm = llm
        self.registry = tool_registry or create_default_registry()
        self.inject_failures = inject_failures or []
        self.settings = get_settings()

    async def run(self, query: str) -> AsyncIterator[PipelineEvent]:
        """Run the full pipeline, yielding events."""
        run_id = str(uuid.uuid4())[:8]
        start_time = time.monotonic()

        try:
            # ── Stage 1: Plan ─────────────────────────────────────────
            yield PipelineEvent(type=EventType.STAGE_STARTED, run_id=run_id, stage="planner")
            plan = await self._run_agent(
                PlannerAgent(llm=self.llm, max_iterations=self.settings.pipeline_max_agent_iterations),
                PlannerInput(query=query),
            )

            if plan is None:
                yield PipelineEvent(type=EventType.RUN_FAILED, run_id=run_id, data={"error": "Planner failed"})
                return

            yield PipelineEvent(
                type=EventType.STAGE_COMPLETED, run_id=run_id, stage="planner",
                data={"task_count": len(plan.tasks)},
                latency_ms=int((time.monotonic() - start_time) * 1000),
            )

            # ── Stage 2: Research (parallel) ──────────────────────────
            yield PipelineEvent(type=EventType.STAGE_STARTED, run_id=run_id, stage="research")
            findings, failed_tasks = await self._run_research(plan, run_id)

            if not findings:
                yield PipelineEvent(type=EventType.RUN_FAILED, run_id=run_id, data={"error": "All research tasks failed"})
                return

            if failed_tasks:
                yield PipelineEvent(
                    type=EventType.WARNING, run_id=run_id,
                    data={"message": f"Research degraded: {len(failed_tasks)}/{len(plan.tasks)} tasks failed"},
                )

            yield PipelineEvent(
                type=EventType.STAGE_COMPLETED, run_id=run_id, stage="research",
                data={"findings": len(findings), "failed": len(failed_tasks)},
                latency_ms=int((time.monotonic() - start_time) * 1000),
            )

            # ── Stage 3: Analyze ──────────────────────────────────────
            yield PipelineEvent(type=EventType.STAGE_STARTED, run_id=run_id, stage="analyst")
            analysis = await self._run_agent(
                AnalystAgent(llm=self.llm, max_iterations=self.settings.pipeline_max_agent_iterations),
                AnalystInput(query=query, findings=findings, failed_tasks=failed_tasks),
            )

            if analysis is None:
                analysis = Analysis(
                    key_insights=[], risks=[],
                    open_questions=["Analysis could not be completed"],
                    evidence_refs=[], degraded=True, failed_tasks=failed_tasks,
                )
                yield PipelineEvent(type=EventType.WARNING, run_id=run_id, data={"message": "Analysis failed, using partial results"})

            yield PipelineEvent(
                type=EventType.STAGE_COMPLETED, run_id=run_id, stage="analyst",
                data={"insights": len(analysis.key_insights), "risks": len(analysis.risks)},
                latency_ms=int((time.monotonic() - start_time) * 1000),
            )

            # ── Stage 4: Write ────────────────────────────────────────
            yield PipelineEvent(type=EventType.STAGE_STARTED, run_id=run_id, stage="writer")
            report = await self._run_agent(
                WriterAgent(llm=self.llm, max_iterations=self.settings.pipeline_max_agent_iterations),
                WriterInput(query=query, analysis=analysis, findings=findings, revision_notes=""),
            )

            if report is None:
                report = FinalReport(
                    title="Research Report (Incomplete)",
                    executive_summary="Report generation encountered issues.",
                    sections=[], citations=[],
                    degraded_coverage=True, coverage_note="Writer stage failed.",
                )

            yield PipelineEvent(
                type=EventType.STAGE_COMPLETED, run_id=run_id, stage="writer",
                data={"sections": len(report.sections)},
                latency_ms=int((time.monotonic() - start_time) * 1000),
            )

            # ── Stage 5: Validate ─────────────────────────────────────
            yield PipelineEvent(type=EventType.STAGE_STARTED, run_id=run_id, stage="validator")
            validation = await self._run_agent(
                ValidatorAgent(llm=self.llm, max_iterations=self.settings.pipeline_max_agent_iterations),
                ValidatorInput(report=report, findings=findings),
            )

            if validation is None:
                validation = ValidationResult(
                    passed=True, issues=[], score=0.5,
                    summary="Validator produced no output; accepting with caution.",
                )

            yield PipelineEvent(
                type=EventType.STAGE_COMPLETED, run_id=run_id, stage="validator",
                data={"passed": validation.passed, "score": validation.score},
                latency_ms=int((time.monotonic() - start_time) * 1000),
            )

            # ── Revision loop (if needed) ─────────────────────────────
            if not validation.passed:
                revision_notes = "; ".join(
                    f"{i.issue_type}: {i.description}" for i in validation.issues
                )
                logger.info("Validation failed, revising: %s", revision_notes[:200])
                yield PipelineEvent(
                    type=EventType.STAGE_RETRY, run_id=run_id, stage="writer",
                    data={"reason": "validation_failed", "issues": len(validation.issues)},
                )

                revised = await self._run_agent(
                    WriterAgent(llm=self.llm, max_iterations=self.settings.pipeline_max_agent_iterations),
                    WriterInput(query=query, analysis=analysis, findings=findings, revision_notes=revision_notes),
                )
                if revised is not None:
                    report = revised

            # ── Done ──────────────────────────────────────────────────
            elapsed = int((time.monotonic() - start_time) * 1000)
            yield PipelineEvent(
                type=EventType.RUN_COMPLETED, run_id=run_id,
                data={"report_title": report.title, "sections": len(report.sections), "citations": len(report.citations)},
                latency_ms=elapsed,
            )

        except PipelineError as e:
            yield PipelineEvent(type=EventType.RUN_FAILED, run_id=run_id, data={"error": str(e)})
        except Exception as e:
            logger.exception("Unexpected pipeline error")
            yield PipelineEvent(type=EventType.RUN_FAILED, run_id=run_id, data={"error": f"Unexpected: {type(e).__name__}: {e}"})

    async def _run_agent(self, agent: Any, input_data: Any) -> Any:
        """Run an agent through its tool-use loop and return the output."""
        messages: list[LLMMessage] = [
            LLMMessage(role="user", content=agent._format_input(input_data))
        ]
        tool_defs = agent._get_tool_definitions()

        for _iteration in range(agent.max_iterations):
            response = await agent.llm.complete(
                system=agent.system_prompt,
                messages=messages,
                tools=tool_defs,
            )

            if response.has_tool_calls:
                submit_calls = [tc for tc in response.tool_calls if tc.name == "submit_result"]
                other_calls = [tc for tc in response.tool_calls if tc.name != "submit_result"]

                # Execute non-submit tools
                tool_results_content: list[dict[str, Any]] = []
                for tc in other_calls:
                    tool_obj = next((t for t in agent.tools if t.name == tc.name), None)
                    if tool_obj:
                        result = await tool_obj.execute(tc.input)
                        tool_results_content.append({
                            "type": "tool_result",
                            "tool_use_id": tc.id,
                            "content": result.content,
                        })

                # Build assistant message
                assistant_content: list[dict[str, Any]] = []
                if response.content:
                    assistant_content.append({"type": "text", "text": response.content})
                for tc in response.tool_calls:
                    assistant_content.append({
                        "type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.input,
                    })
                messages.append(LLMMessage(role="assistant", content=assistant_content))

                if tool_results_content:
                    messages.append(LLMMessage(role="user", content=tool_results_content))

                # Try to parse submit_result
                if submit_calls:
                    output = agent._try_parse_output(submit_calls[0].input)
                    if output is not None:
                        return output
                    # Repair turn
                    error_msg = agent._get_validation_error(submit_calls[0].input)
                    messages.append(LLMMessage(
                        role="user",
                        content=f"Validation error:\n{error_msg}\nPlease fix and resubmit using submit_result.",
                    ))
            else:
                if response.content:
                    output = agent._try_parse_output_from_text(response.content)
                    if output is not None:
                        return output
                    messages.append(LLMMessage(role="assistant", content=response.content))
                    messages.append(LLMMessage(
                        role="user",
                        content="Please use the submit_result tool to provide your structured output.",
                    ))

        return None

    async def _run_research(
        self, plan: ResearchPlan, run_id: str
    ) -> tuple[list[ResearchFindings], list[str]]:
        """Run research tasks in parallel with bounded concurrency."""
        semaphore = asyncio.Semaphore(self.settings.pipeline_research_concurrency)

        async def run_single_task(task: ResearchTask) -> ResearchFindings | None:
            async with semaphore:
                try:
                    # Check for injected failures
                    if any(t in self.inject_failures for t in task.suggested_tools):
                        raise StageError("researcher", f"Injected failure for task {task.id}")

                    tools: list[Tool] = self.registry.get_many(task.suggested_tools) or self.registry.all_tools()  # type: ignore[assignment]
                    agent = ResearcherAgent(
                        tools=tools,
                        llm=self.llm,
                        max_iterations=self.settings.pipeline_max_agent_iterations,
                    )

                    output = await with_timeout(
                        self._run_agent(
                            agent,
                            ResearcherInput(
                                task_id=task.id,
                                question=task.question,
                                suggested_tools=task.suggested_tools,
                            ),
                        ),
                        self.settings.pipeline_stage_timeout_s,
                        f"researcher_{task.id}",
                    )
                    return output

                except Exception as e:
                    logger.warning("Research task %s failed: %s", task.id, e)
                    return None

        results = await asyncio.gather(*[run_single_task(task) for task in plan.tasks])

        findings: list[ResearchFindings] = []
        failed_tasks: list[str] = []
        for i, result in enumerate(results):
            task = plan.tasks[i]
            if result is None:
                failed_tasks.append(task.id)
            else:
                findings.append(result)

        return findings, failed_tasks
