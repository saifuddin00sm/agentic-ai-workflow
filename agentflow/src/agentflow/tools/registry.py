"""Tool registry - central place to register and look up tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentflow.tools import Tool


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}  # type: ignore[type-arg]

    def register(self, tool: Tool) -> None:  # type: ignore[type-arg]
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:  # type: ignore[type-arg]
        """Get a tool by name."""
        return self._tools.get(name)

    def get_many(self, names: list[str]) -> list[Tool]:  # type: ignore[type-arg]
        """Get multiple tools by name."""
        return [self._tools[n] for n in names if n in self._tools]

    def all_tools(self) -> list[Tool]:  # type: ignore[type-arg]
        """Get all registered tools."""
        return list(self._tools.values())

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())


def create_default_registry() -> ToolRegistry:
    """Create a registry with all default tools."""
    from agentflow.tools.news import NewsTool
    from agentflow.tools.sec import SecFilingsTool
    from agentflow.tools.stocks import StockTool
    from agentflow.tools.web_search import WebSearchTool
    from agentflow.tools.wikipedia import WikipediaTool

    registry = ToolRegistry()
    registry.register(WikipediaTool())
    registry.register(NewsTool())
    registry.register(StockTool())
    registry.register(SecFilingsTool())

    # Only register web search if API key is available
    web_search = WebSearchTool()
    if web_search.available:
        registry.register(web_search)

    return registry
