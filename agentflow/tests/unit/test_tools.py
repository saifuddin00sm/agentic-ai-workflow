"""Tests for tools with mocked HTTP."""

from __future__ import annotations

import pytest
import httpx
import respx

from agentflow.tools.wikipedia import WikipediaTool, WikipediaInput
from agentflow.tools.news import NewsTool, NewsInput
from fixtures import WIKIPEDIA_SUMMARY, WIKIPEDIA_SEARCH, GDELT_RESPONSE


class TestWikipediaTool:
    """Tests for the Wikipedia tool."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_summary_success(self) -> None:
        respx.get("https://en.wikipedia.org/api/rest_v1/page/summary/TestTopic").mock(
            return_value=httpx.Response(200, json=WIKIPEDIA_SUMMARY)
        )

        tool = WikipediaTool()
        result = await tool.execute({"query": "TestTopic", "action": "summary"})

        assert not result.is_error
        assert "Acme Corp" in result.content
        assert "enterprise software" in result.content

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_success(self) -> None:
        respx.get("https://en.wikipedia.org/w/api.php").mock(
            return_value=httpx.Response(200, json=WIKIPEDIA_SEARCH)
        )

        tool = WikipediaTool()
        result = await tool.execute({"query": "Acme", "action": "search"})

        assert not result.is_error
        assert "Acme Corp" in result.content

    @pytest.mark.asyncio
    @respx.mock
    async def test_summary_fallback_to_search(self) -> None:
        # Summary returns 404
        respx.get("https://en.wikipedia.org/api/rest_v1/page/summary/NonExistent").mock(
            return_value=httpx.Response(404)
        )
        # Search succeeds
        respx.get("https://en.wikipedia.org/w/api.php").mock(
            return_value=httpx.Response(200, json=WIKIPEDIA_SEARCH)
        )

        tool = WikipediaTool()
        result = await tool.execute({"query": "NonExistent", "action": "summary"})

        assert not result.is_error
        assert "Found" in result.content

    @pytest.mark.asyncio
    async def test_invalid_input(self) -> None:
        tool = WikipediaTool()
        result = await tool.execute({"query": "", "action": "invalid_action"})

        assert result.is_error
        assert "Error" in result.content

    def test_schema_generation(self) -> None:
        tool = WikipediaTool()
        schema = tool.get_schema()
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "action" in schema["properties"]


class TestNewsTool:
    """Tests for the GDELT news tool."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_success(self) -> None:
        respx.get("https://api.gdeltproject.org/api/v2/doc/doc").mock(
            return_value=httpx.Response(200, json=GDELT_RESPONSE)
        )

        tool = NewsTool()
        result = await tool.execute({"query": "Acme Corp", "max_records": 5})

        assert not result.is_error
        assert "Acme Corp" in result.content
        assert "Q4 Results" in result.content

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_results(self) -> None:
        respx.get("https://api.gdeltproject.org/api/v2/doc/doc").mock(
            return_value=httpx.Response(200, json={"articles": []})
        )

        tool = NewsTool()
        result = await tool.execute({"query": "Nonexistent Company XYZ"})

        assert not result.is_error
        assert "No news articles" in result.content

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_error(self) -> None:
        respx.get("https://api.gdeltproject.org/api/v2/doc/doc").mock(
            return_value=httpx.Response(500)
        )

        tool = NewsTool()
        result = await tool.execute({"query": "test"})

        assert result.is_error
        assert "500" in result.content
