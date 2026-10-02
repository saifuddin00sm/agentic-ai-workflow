"""CLI application using typer + rich."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.tree import Tree

from agentflow.config import get_settings
from agentflow.logging import setup_logging
from agentflow.models.events import EventType, PipelineEvent

app = typer.Typer(name="agentflow", help="Multi-agent research & analysis workflow")
console = Console()


def _create_mock_client():  # type: ignore[no-untyped-def]
    """Create a mock client with scripted responses for demo."""
    from agentflow.llm.mock_client import MockLLMClient
    from agentflow.llm import LLMResponse, ToolCall

    client = MockLLMClient()

    # Planner response
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="plan_1",
            name="submit_result",
            input={
                "query": "Company due-diligence brief on Acme Corp",
                "company": "Acme Corp",
                "tasks": [
                    {"id": "task_1", "question": "What does Acme Corp do?", "suggested_tools": ["wikipedia"], "priority": 1},
                    {"id": "task_2", "question": "Financial performance?", "suggested_tools": ["stocks"], "priority": 1},
                    {"id": "task_3", "question": "Recent news?", "suggested_tools": ["news"], "priority": 2},
                ],
                "approach": "Comprehensive due diligence.",
            },
        )],
        stop_reason="tool_use",
    ))

    # Researcher responses
    for task_id, question, claims in [
        ("task_1", "What does Acme Corp do?", [
            {"text": "Acme Corp is a technology company specializing in enterprise software.", "source_url": "https://en.wikipedia.org/wiki/Acme_Corp", "source_name": "Wikipedia", "confidence": 0.9, "evidence_id": "ev_1"},
            {"text": "Founded in 2005, headquartered in San Francisco.", "source_url": "https://en.wikipedia.org/wiki/Acme_Corp", "source_name": "Wikipedia", "confidence": 0.85, "evidence_id": "ev_2"},
        ]),
        ("task_2", "Financial performance?", [
            {"text": "Market cap of approximately $2.5 billion.", "source_url": "https://finance.yahoo.com/quote/ACME", "source_name": "Yahoo Finance", "confidence": 0.8, "evidence_id": "ev_3"},
            {"text": "Revenue grew 15% YoY to $800M in FY2024.", "source_url": "https://sec.gov/acme-10k", "source_name": "SEC Filing", "confidence": 0.9, "evidence_id": "ev_4"},
        ]),
        ("task_3", "Recent news?", [
            {"text": "Strategic partnership with TechGiant Inc announced Q1 2025.", "source_url": "https://news.example.com/acme", "source_name": "TechNews", "confidence": 0.85, "evidence_id": "ev_5"},
            {"text": "Expanded into Europe with offices in London and Berlin.", "source_url": "https://news.example.com/acme-eu", "source_name": "BusinessDaily", "confidence": 0.8, "evidence_id": "ev_6"},
        ]),
    ]:
        client.add_response(LLMResponse(
            content="",
            tool_calls=[ToolCall(
                id=f"res_{task_id}",
                name="submit_result",
                input={
                    "task_id": task_id,
                    "question": question,
                    "claims": claims,
                    "summary": f"Findings for: {question}",
                    "tool_calls_made": 2,
                },
            )],
            stop_reason="tool_use",
        ))

    # Analyst response
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="analyst_1",
            name="submit_result",
            input={
                "key_insights": [
                    {"text": "Strong revenue growth (15% YoY) with expanding market presence.", "supporting_evidence": ["ev_4", "ev_3"], "confidence": 0.85},
                    {"text": "European expansion represents growth opportunity.", "supporting_evidence": ["ev_6"], "confidence": 0.75},
                ],
                "risks": [
                    {"description": "Key person dependency on founding CEO", "severity": "medium", "supporting_evidence": ["ev_2"]},
                ],
                "open_questions": ["Customer concentration metrics unavailable"],
                "evidence_refs": ["ev_1", "ev_2", "ev_3", "ev_4", "ev_5", "ev_6"],
                "degraded": False,
                "failed_tasks": [],
            },
        )],
        stop_reason="tool_use",
    ))

    # Writer response
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="writer_1",
            name="submit_result",
            input={
                "title": "Due Diligence Brief: Acme Corp",
                "executive_summary": "Acme Corp is a San Francisco-based enterprise software company founded in 2005. The company demonstrates strong financial performance with $800M in FY2024 revenue (15% YoY growth) and a $2.5B market cap. Recent developments include a strategic partnership with TechGiant Inc and European expansion.",
                "sections": [
                    {"title": "Company Overview", "content": "Acme Corp is a technology company specializing in enterprise software [ev_1]. Founded in 2005, headquartered in San Francisco [ev_2].", "subsections": []},
                    {"title": "Financial Performance", "content": "Market cap of $2.5B [ev_3]. Revenue grew 15% YoY to $800M [ev_4].", "subsections": []},
                    {"title": "Recent Developments", "content": "Partnership with TechGiant Inc [ev_5]. European expansion to London and Berlin [ev_6].", "subsections": []},
                ],
                "citations": [
                    {"evidence_id": "ev_1", "source_url": "https://en.wikipedia.org/wiki/Acme_Corp", "source_name": "Wikipedia", "claim_text": "Enterprise software"},
                    {"evidence_id": "ev_2", "source_url": "https://en.wikipedia.org/wiki/Acme_Corp", "source_name": "Wikipedia", "claim_text": "Founded 2005"},
                    {"evidence_id": "ev_3", "source_url": "https://finance.yahoo.com/quote/ACME", "source_name": "Yahoo Finance", "claim_text": "$2.5B market cap"},
                    {"evidence_id": "ev_4", "source_url": "https://sec.gov/acme-10k", "source_name": "SEC Filing", "claim_text": "$800M revenue"},
                    {"evidence_id": "ev_5", "source_url": "https://news.example.com/acme", "source_name": "TechNews", "claim_text": "TechGiant partnership"},
                    {"evidence_id": "ev_6", "source_url": "https://news.example.com/acme-eu", "source_name": "BusinessDaily", "claim_text": "European expansion"},
                ],
                "degraded_coverage": False,
                "coverage_note": "",
            },
        )],
        stop_reason="tool_use",
    ))

    # Validator response
    client.add_response(LLMResponse(
        content="",
        tool_calls=[ToolCall(
            id="val_1",
            name="submit_result",
            input={
                "passed": True,
                "issues": [],
                "score": 0.92,
                "summary": "Report passes validation. All claims properly cited.",
            },
        )],
        stop_reason="tool_use",
    ))

    return client


@app.command()
def run(
    query: str = typer.Argument(..., help="Research query"),
    mock: bool = typer.Option(False, "--mock", help="Run offline with mock data"),
    json_output: bool = typer.Option(False, "--json", help="Output trace as JSON"),
    inject_failure: Optional[str] = typer.Option(None, "--inject-failure", help="Inject tool failure"),
) -> None:
    """Run the multi-agent research pipeline."""
    setup_logging()

    async def _run() -> None:
        if mock:
            llm = _create_mock_client()
        else:
            try:
                from agentflow.llm.anthropic_client import AnthropicClient
                llm = AnthropicClient()
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print("Use --mock for offline demo or set ANTHROPIC_API_KEY")
                raise typer.Exit(1)

        from agentflow.pipeline import Pipeline
        failures = [inject_failure] if inject_failure else []
        pipeline = Pipeline(llm=llm, inject_failures=failures)

        events: list[PipelineEvent] = []
        tree = Tree("🔬 [bold]AgentFlow Research Pipeline[/bold]")

        console.print(Panel(f"[bold]Query:[/bold] {query}", title="Research Request"))

        with Live(tree, console=console, refresh_per_second=4) as live:
            async for event in pipeline.run(query):
                events.append(event)

                if event.type == EventType.STAGE_STARTED:
                    tree.add(f"▶ {event.stage}")
                elif event.type == EventType.STAGE_COMPLETED:
                    tree.add(f"✓ [green]{event.stage}[/green] ({event.latency_ms}ms)")
                elif event.type == EventType.TOOL_CALLED:
                    tree.add(f"  🔧 {event.data.get('tool', '?')}")
                elif event.type == EventType.TOOL_RESULT:
                    tree.add(f"  ✓ {event.data.get('tool', '?')}")
                elif event.type == EventType.TOOL_FAILED:
                    tree.add(f"  ✗ [yellow]{event.data.get('tool', '?')}[/yellow]")
                elif event.type == EventType.WARNING:
                    tree.add(f"⚠ [yellow]{event.data.get('message', '')}[/yellow]")
                elif event.type == EventType.STAGE_RETRY:
                    tree.add(f"↻ [yellow]Revision: {event.stage}[/yellow]")
                elif event.type == EventType.RUN_COMPLETED:
                    tree.add(f"🏁 [bold green]Completed[/bold green] ({event.latency_ms}ms)")
                elif event.type == EventType.RUN_FAILED:
                    tree.add(f"💥 [bold red]Failed:[/bold red] {event.data.get('error', '')}")

                live.update(tree)

        if json_output:
            trace = [e.model_dump(mode="json") for e in events]
            console.print("\n" + json.dumps(trace, indent=2, default=str))

    asyncio.run(_run())


@app.command()
def demo() -> None:
    """Run a quick demo with mock data."""
    run("Company due-diligence brief on Acme Corp", mock=True)


if __name__ == "__main__":
    app()
