"""Agent base class - generic tool-use loop with structured output."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, AsyncIterator, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from agentflow.llm import LLMClient, LLMMessage, LLMResponse, ToolDefinition
from agentflow.models.events import EventType, PipelineEvent
from agentflow.resilience import StageOutputError
from agentflow.tools import Tool, ToolResult

logger = logging.getLogger(__name__)

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a system prompt from the prompts directory."""
    path = PROMPTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text().strip()
    logger.warning("Prompt file not found: %s", path)
    return f"You are a helpful assistant. ({name})"


class Agent(Generic[TInput, TOutput]):
    """Generic agent with tool-use loop and structured output.

    Inputs:
    - system_prompt: agent's system prompt
    - input_model: Pydantic model for the agent's input
    - output_model: Pydantic model for the agent's output
    - tools: list of tools available to this agent
    - max_iterations: max tool-use loop iterations
    """

    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        input_model: type[TInput],
        output_model: type[TOutput],
        tools: list[Tool] | None = None,  # type: ignore[type-arg]
        llm: LLMClient | None = None,
        max_iterations: int = 10,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.input_model = input_model
        self.output_model = output_model
        self.tools = tools or []
        self.llm = llm
        self.max_iterations = max_iterations

        # Build submit_result tool from output model schema
        self._submit_tool = ToolDefinition(
            name="submit_result",
            description=f"Submit your final result. Must conform to the output schema.",
            input_schema=self._get_output_schema(),
        )

    def _get_output_schema(self) -> dict[str, Any]:
        """Get JSON schema for the output model, simplified for LLM."""
        schema = self.output_model.model_json_schema()
        # Remove $defs references that confuse some models
        if "$defs" in schema:
            del schema["$defs"]
        return schema

    def _get_tool_definitions(self) -> list[ToolDefinition]:
        """Get tool definitions including submit_result."""
        defs = [
            ToolDefinition(
                name=t.name,
                description=t.description,
                input_schema=t.get_schema(),
            )
            for t in self.tools
        ]
        defs.append(self._submit_tool)
        return defs

    async def run(
        self,
        input_data: TInput,
        run_id: str = "",
    ) -> AsyncIterator[PipelineEvent]:
        """Run the agent with the tool-use loop.

        Yields PipelineEvents for progress tracking.
        Returns the final validated output.
        """
        if self.llm is None:
            raise ValueError(f"Agent {self.name}: LLM client not set")

        start_time = time.monotonic()
        messages: list[LLMMessage] = [
            LLMMessage(role="user", content=self._format_input(input_data))
        ]
        tool_defs = self._get_tool_definitions()

        output: TOutput | None = None
        attempts = 0

        for iteration in range(self.max_iterations):
            attempts += 1

            # Call LLM
            response: LLMResponse = await self.llm.complete(
                system=self.system_prompt,
                messages=messages,
                tools=tool_defs,
            )

            # Check if model wants to use tools
            if response.has_tool_calls:
                # Check if it's the submit_result tool
                submit_calls = [tc for tc in response.tool_calls if tc.name == "submit_result"]
                other_calls = [tc for tc in response.tool_calls if tc.name != "submit_result"]

                # Execute non-submit tools
                tool_results: list[dict[str, Any]] = []
                for tc in other_calls:
                    yield PipelineEvent(
                        type=EventType.TOOL_CALLED,
                        run_id=run_id,
                        stage=self.name,
                        data={"tool": tc.name, "args": tc.input},
                    )

                    result = await self._execute_tool(tc.name, tc.input)

                    yield PipelineEvent(
                        type=EventType.TOOL_RESULT if not result.is_error else EventType.TOOL_FAILED,
                        run_id=run_id,
                        stage=self.name,
                        data={
                            "tool": tc.name,
                            "summary": result.content[:200],
                            "is_error": result.is_error,
                        },
                        latency_ms=result.metadata.get("latency_ms", 0),
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": result.content,
                    })

                # Add assistant message with tool calls
                assistant_content: list[dict[str, Any]] = []
                if response.content:
                    assistant_content.append({"type": "text", "text": response.content})
                for tc in response.tool_calls:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    })

                messages.append(LLMMessage(role="assistant", content=assistant_content))

                # Add tool results
                if tool_results:
                    messages.append(LLMMessage(role="user", content=tool_results))

                # If there were submit calls, try to parse the output
                if submit_calls:
                    output = self._try_parse_output(submit_calls[0].input)
                    if output is not None:
                        break
                    # Repair turn: re-prompt with error
                    else:
                        error_msg = self._get_validation_error(submit_calls[0].input)
                        messages.append(LLMMessage(
                            role="user",
                            content=f"Your previous output had validation errors:\n{error_msg}\n\nPlease fix and resubmit using submit_result.",
                        ))
                        yield PipelineEvent(
                            type=EventType.STAGE_RETRY,
                            run_id=run_id,
                            stage=self.name,
                            data={"reason": "output_validation_failed", "error": error_msg[:200]},
                        )
            else:
                # No tool calls - try to parse text as output
                if response.content:
                    output = self._try_parse_output_from_text(response.content)
                    if output is not None:
                        break
                    # If text can't be parsed, add instruction to use submit_result
                    messages.append(LLMMessage(
                        role="assistant",
                        content=response.content,
                    ))
                    messages.append(LLMMessage(
                        role="user",
                        content="Please use the submit_result tool to provide your structured output.",
                    ))

        if output is None:
            raise StageOutputError(
                self.name,
                f"Failed to produce valid output after {attempts} iterations",
            )

        elapsed = int((time.monotonic() - start_time) * 1000)
        yield PipelineEvent(
            type=EventType.STAGE_COMPLETED,
            run_id=run_id,
            stage=self.name,
            data={"attempts": attempts},
            latency_ms=elapsed,
        )

    async def _execute_tool(self, name: str, input: dict[str, Any]) -> ToolResult:  # noqa: A002
        """Execute a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return await tool.execute(input)
        return ToolResult(content=f"Unknown tool: {name}", is_error=True)

    def _try_parse_output(self, raw: dict[str, Any]) -> TOutput | None:
        """Try to parse tool input as the output model."""
        try:
            return self.output_model.model_validate(raw)
        except ValidationError:
            return None

    def _try_parse_output_from_text(self, text: str) -> TOutput | None:
        """Try to parse text content as JSON output."""
        # Try direct JSON parse
        try:
            data = json.loads(text)
            return self.output_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            pass

        # Try to find JSON block in text
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
            return self.output_model.model_validate(data)
        except (ValueError, json.JSONDecodeError, ValidationError):
            pass

        return None

    def _get_validation_error(self, raw: dict[str, Any]) -> str:
        """Get validation error message for repair prompt."""
        try:
            self.output_model.model_validate(raw)
            return ""
        except ValidationError as e:
            return str(e)

    def _format_input(self, input_data: TInput) -> str:
        """Format input for the LLM."""
        return input_data.model_dump_json(indent=2)
