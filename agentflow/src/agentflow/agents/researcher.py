"""Researcher agent - executes a single research task."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.agents import Agent, load_prompt
from agentflow.models.findings import ResearchFindings
from agentflow.tools import Tool


class ResearcherInput(BaseModel):
    """Input to a researcher agent."""

    task_id: str = Field(description="ID of the research task")
    question: str = Field(description="Question to research")
    suggested_tools: list[str] = Field(default_factory=list)


class ResearcherAgent(Agent[ResearcherInput, ResearchFindings]):
    """Agent that researches a single question using tools."""

    def __init__(self, *, tools: list[Tool], **kwargs: object) -> None:  # type: ignore[type-arg]
        super().__init__(
            name="researcher",
            system_prompt=load_prompt("researcher"),
            input_model=ResearcherInput,
            output_model=ResearchFindings,
            tools=tools,
            **kwargs,  # type: ignore[arg-type]
        )
