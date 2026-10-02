"""Analysis models - output of AnalystAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Insight(BaseModel):
    """A key insight derived from findings."""

    text: str = Field(description="The insight")
    supporting_evidence: list[str] = Field(
        description="Evidence IDs supporting this insight"
    )
    confidence: float = Field(ge=0.0, le=1.0)


class Risk(BaseModel):
    """An identified risk."""

    description: str = Field(description="Risk description")
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    supporting_evidence: list[str] = Field(description="Evidence IDs")


class Analysis(BaseModel):
    """Output of the AnalystAgent."""

    key_insights: list[Insight] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    open_questions: list[str] = Field(
        default_factory=list, description="Questions that couldn't be answered"
    )
    evidence_refs: list[str] = Field(
        description="All evidence IDs used in this analysis"
    )
    degraded: bool = Field(default=False, description="True if some research tasks failed")
    failed_tasks: list[str] = Field(
        default_factory=list, description="IDs of failed research tasks"
    )
