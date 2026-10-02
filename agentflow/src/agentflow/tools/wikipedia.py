"""Wikipedia tool - REST API for summaries and search."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.tools import ToolResult, Tool, http_get


class WikipediaInput(BaseModel):
    """Input for Wikipedia tool."""

    query: str = Field(description="Search query or article title")
    action: str = Field(default="summary", pattern="^(summary|search)$", description="Action: summary or search")


class WikipediaTool(Tool[WikipediaInput]):
    """Wikipedia REST API tool."""

    name = "wikipedia"
    description = "Search Wikipedia or get article summaries. Use 'summary' for a specific topic, 'search' to find articles."
    input_model = WikipediaInput

    async def run(self, input: WikipediaInput) -> ToolResult:  # noqa: A002
        if input.action == "search":
            return await self._search(input.query)
        return await self._summary(input.query)

    async def _search(self, query: str) -> ToolResult:
        resp = await http_get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": "5",
            },
        )
        data = resp.json()
        results = data.get("query", {}).get("search", [])
        if not results:
            return ToolResult(content=f"No Wikipedia results for: {query}")

        lines = [f"Found {len(results)} results for '{query}':"]
        for r in results:
            lines.append(f"- {r['title']}: {r.get('snippet', '')[:150]}")
        return ToolResult(content="\n".join(lines))

    async def _summary(self, topic: str) -> ToolResult:
        # First try direct summary
        resp = await http_get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
        )
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", topic)
            extract = data.get("extract", "No summary available.")
            return ToolResult(
                content=f"# {title}\n\n{extract}",
                metadata={"source_url": f"https://en.wikipedia.org/wiki/{topic}"},
            )

        # Fall back to search
        return await self._search(topic)
