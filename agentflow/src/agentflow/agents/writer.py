"""Writer agent - produces the final report."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.agents import Agent, load_prompt
from agentflow.models.analysis import Analysis
from agentflow.models.findings import ResearchFindings
from agentflow.models.report import FinalReport


class WriterInput(BaseModel):
    """Input to the writer agent."""

    query: str = Field(description="Original research query")
    analysis: Analysis = Field(description="Analysis to write up")
    findings: list[ResearchFindings] = Field(description="Source findings for citations")
    revision_notes: str = Field(default="", description="Notes from validator if revising")


class WriterAgent(Agent[WriterInput, FinalReport]):
    """Agent that writes the final report."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="writer",
            system_prompt=load_prompt("writer"),
            input_model=WriterInput,
            output_model=FinalReport,
            tools=[],  # Writer works from analysis only
            **kwargs,  # type: ignore[arg-type]
        )
