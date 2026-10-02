"""Report models - output of WriterAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Section(BaseModel):
    """A section of the final report."""

    title: str = Field(description="Section heading")
    content: str = Field(description="Section body text with inline citations [ev_N]")
    subsections: list[Section] = Field(default_factory=list)


class Citation(BaseModel):
    """A citation in the report."""

    evidence_id: str = Field(description="Evidence reference ID")
    source_url: str = Field(description="Source URL")
    source_name: str = Field(default="")
    claim_text: str = Field(default="", description="What this evidence supports")


class FinalReport(BaseModel):
    """Output of the WriterAgent."""

    title: str = Field(description="Report title")
    executive_summary: str = Field(
        description="Executive summary (max 150 words)",
        max_length=1200,
    )
    sections: list[Section] = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    degraded_coverage: bool = Field(
        default=False,
        description="True if report has reduced coverage due to failures",
    )
    coverage_note: str = Field(
        default="",
        description="Note about any coverage gaps",
    )
