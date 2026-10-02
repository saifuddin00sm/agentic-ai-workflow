"""Validation result model - output of ValidatorAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """A single validation issue."""

    issue_type: str = Field(
        pattern="^(uncited_claim|unsupported_claim|missing_section|schema_error|other)$",
        description="Type of validation issue",
    )
    description: str = Field(description="Description of the issue")
    location: str = Field(default="", description="Where in the report the issue is")


class ValidationResult(BaseModel):
    """Output of the ValidatorAgent."""

    passed: bool = Field(description="Whether the report passed validation")
    issues: list[ValidationIssue] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0, description="Overall quality score 0-1")
    summary: str = Field(description="Brief validation summary")
