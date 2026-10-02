"""Analyst agent - synthesizes findings into analysis."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.agents import Agent, load_prompt
from agentflow.models.analysis import Analysis
from agentflow.models.findings import ResearchFindings


class AnalystInput(BaseModel):
    """Input to the analyst agent."""

    query: str = Field(description="Original research query")
    findings: list[ResearchFindings] = Field(description="All research findings")
    failed_tasks: list[str] = Field(default_factory=list, description="IDs of failed tasks")


class AnalystAgent(Agent[AnalystInput, Analysis]):
    """Agent that analyzes research findings."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="analyst",
            system_prompt=load_prompt("analyst"),
            input_model=AnalystInput,
            output_model=Analysis,
            tools=[],  # Analyst works from findings only
            **kwargs,  # type: ignore[arg-type]
        )
