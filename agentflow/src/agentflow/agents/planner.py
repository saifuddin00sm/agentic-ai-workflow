"""Planner agent - creates research plan from user query."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.agents import Agent, load_prompt
from agentflow.models.plan import ResearchPlan


class PlannerInput(BaseModel):
    """Input to the planner."""

    query: str = Field(description="User's research query")


class PlannerAgent(Agent[PlannerInput, ResearchPlan]):
    """Agent that creates a research plan from a query."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="planner",
            system_prompt=load_prompt("planner"),
            input_model=PlannerInput,
            output_model=ResearchPlan,
            tools=[],  # Planner doesn't need tools
            **kwargs,  # type: ignore[arg-type]
        )
