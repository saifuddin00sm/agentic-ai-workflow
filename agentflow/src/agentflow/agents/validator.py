"""Validator agent - checks report quality."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.agents import Agent, load_prompt
from agentflow.models.findings import ResearchFindings
from agentflow.models.report import FinalReport
from agentflow.models.validation import ValidationResult


class ValidatorInput(BaseModel):
    """Input to the validator agent."""

    report: FinalReport = Field(description="Report to validate")
    findings: list[ResearchFindings] = Field(description="Source findings for cross-check")


class ValidatorAgent(Agent[ValidatorInput, ValidationResult]):
    """Agent that validates the final report."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="validator",
            system_prompt=load_prompt("validator"),
            input_model=ValidatorInput,
            output_model=ValidationResult,
            tools=[],  # Validator doesn't use tools
            **kwargs,  # type: ignore[arg-type]
        )
