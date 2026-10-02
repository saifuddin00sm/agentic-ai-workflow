"""Research plan models - output of PlannerAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchTask(BaseModel):
    """A single research sub-task."""

    id: str = Field(description="Unique task identifier, e.g. 'task_1'")
    question: str = Field(description="The specific question to research")
    suggested_tools: list[str] = Field(
        default_factory=list,
        description="Tool names suggested for this task",
    )
    priority: int = Field(default=1, ge=1, le=5, description="Priority 1=highest")


class ResearchPlan(BaseModel):
    """Output of the PlannerAgent."""

    query: str = Field(description="Original user query")
    company: str = Field(description="Company name being researched")
    tasks: list[ResearchTask] = Field(
        description="List of research tasks to execute",
        min_length=1,
    )
    approach: str = Field(description="Brief description of the research approach")
