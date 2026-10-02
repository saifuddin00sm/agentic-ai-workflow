"""GDELT News tool - DOC 2.0 API for recent coverage."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.tools import ToolResult, Tool, http_get


class NewsInput(BaseModel):
    """Input for GDELT news tool."""

    query: str = Field(description="Search query for news articles")
    max_records: int = Field(default=10, ge=1, le=25, description="Max articles to return")
    timespan: str = Field(default="1m", description="Time span: 1m=month, 1w=week, 1d=day")


class NewsTool(Tool[NewsInput]):
    """GDELT DOC 2.0 API tool for news coverage."""

    name = "news"
    description = "Search recent news articles via GDELT. Returns headlines, sources, and URLs. No API key required."
    input_model = NewsInput

    async def run(self, input: NewsInput) -> ToolResult:  # noqa: A002
        resp = await http_get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": input.query,
                "mode": "artlist",
                "format": "json",
                "maxrecords": str(input.max_records),
                "timespan": input.timespan,
                "sort": "date",
            },
        )

        if resp.status_code != 200:
            return ToolResult(
                content=f"GDELT API returned status {resp.status_code}",
                is_error=True,
            )

        data = resp.json()
        articles = data.get("articles", [])

        if not articles:
            return ToolResult(content=f"No news articles found for: {input.query}")

        lines = [f"Found {len(articles)} articles for '{input.query}':\n"]
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            url = article.get("url", "")
            source = article.get("domain", "unknown")
            date = article.get("seendate", "")[:10]
            lines.append(f"{i}. [{source}] {title}")
            lines.append(f"   URL: {url}")
            lines.append(f"   Date: {date}")
            lines.append("")

        return ToolResult(
            content="\n".join(lines),
            metadata={"article_count": len(articles)},
        )
