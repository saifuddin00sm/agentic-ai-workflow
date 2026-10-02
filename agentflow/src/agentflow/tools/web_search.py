"""Tavily web search tool (optional - requires API key)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.config import get_settings
from agentflow.tools import ToolResult, Tool, http_get


class WebSearchInput(BaseModel):
    """Input for web search tool."""

    query: str = Field(description="Search query")
    max_results: int = Field(default=5, ge=1, le=10)
    search_depth: str = Field(default="basic", pattern="^(basic|advanced)$")


class WebSearchTool(Tool[WebSearchInput]):
    """Tavily web search tool. Auto-disabled if no API key."""

    name = "web_search"
    description = "Search the web using Tavily. Returns relevant results with titles, URLs, and snippets."
    input_model = WebSearchInput
    _available: bool = True

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.tavily_api_key
        if not self._api_key:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def run(self, input: WebSearchInput) -> ToolResult:  # noqa: A002
        if not self._available or not self._api_key:
            return ToolResult(
                content="Web search unavailable: TAVILY_API_KEY not set",
                is_error=True,
            )

        resp = await http_get(
            "https://api.tavily.com/search",
            params={
                "api_key": self._api_key,
                "query": input.query,
                "max_results": input.max_results,
                "search_depth": input.search_depth,
            },
        )

        if resp.status_code != 200:
            return ToolResult(
                content=f"Tavily API returned status {resp.status_code}",
                is_error=True,
            )

        data = resp.json()
        results = data.get("results", [])

        if not results:
            return ToolResult(content=f"No web results for: {input.query}")

        lines = [f"Web search results for '{input.query}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.get('title', 'No title')}")
            lines.append(f"   URL: {r.get('url', '')}")
            lines.append(f"   {r.get('content', '')[:200]}")
            lines.append("")

        return ToolResult(content="\n".join(lines), metadata={"result_count": len(results)})
