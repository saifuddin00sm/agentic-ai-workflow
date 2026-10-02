"""Research findings models - output of ResearchAgents."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Claim(BaseModel):
    """A factual claim with source attribution."""

    text: str = Field(description="The claim text")
    source_url: str = Field(description="URL where this was found")
    source_name: str = Field(default="", description="Human-readable source name")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
    evidence_id: str = Field(description="Unique evidence reference ID, e.g. 'ev_1'")


class ResearchFindings(BaseModel):
    """Output of a single ResearchAgent for one task."""

    task_id: str = Field(description="ID of the task this addresses")
    question: str = Field(description="The question that was researched")
    claims: list[Claim] = Field(default_factory=list, description="Factual claims found")
    summary: str = Field(description="Brief summary of findings")
    tool_calls_made: int = Field(default=0, description="Number of tool calls executed")
