"""Test fixtures - recorded tool responses and scripted LLM turns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).parent

# ── Recorded tool responses ──────────────────────────────────────────────────

WIKIPEDIA_SUMMARY: dict[str, Any] = {
    "title": "Acme Corp",
    "extract": "Acme Corp is a fictional technology company used for demonstration purposes. "
    "The company specializes in enterprise software solutions and was founded in 2005.",
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Acme_Corp"}},
}

WIKIPEDIA_SEARCH: dict[str, Any] = {
    "query": {
        "search": [
            {"title": "Acme Corp", "snippet": "Technology company specializing in enterprise software..."},
            {"title": "Acme Corporation (disambiguation)", "snippet": "Acme Corporation may refer to..."},
        ]
    }
}

GDELT_RESPONSE: dict[str, Any] = {
    "articles": [
        {
            "title": "Acme Corp Announces Q4 Results",
            "url": "https://news.example.com/acme-q4",
            "domain": "news.example.com",
            "seendate": "2025-01-15T00:00:00Z",
        },
        {
            "title": "Acme Corp Expands to Europe",
            "url": "https://news.example.com/acme-europe",
            "domain": "business.example.com",
            "seendate": "2025-01-10T00:00:00Z",
        },
    ]
}

SEC_COMPANY_TICKERS: dict[str, Any] = {
    "0": {"cik_str": 1234, "ticker": "ACME", "title": "ACME CORP"},
    "1": {"cik_str": 5678, "ticker": "AAPL", "title": "APPLE INC"},
}

SEC_SUBMISSIONS: dict[str, Any] = {
    "name": "ACME CORP",
    "filings": {
        "recent": {
            "form": ["10-K", "10-Q", "8-K", "10-Q"],
            "filingDate": ["2024-03-15", "2024-08-10", "2024-11-01", "2024-05-10"],
            "accessionNumber": ["0001234-24-001", "0001234-24-002", "0001234-24-003", "0001234-24-004"],
            "primaryDocument": ["acme-10k.htm", "acme-10q_q2.htm", "acme-8k.htm", "acme-10q_q1.htm"],
        }
    },
}


def get_fixture(name: str) -> dict[str, Any]:
    """Get a fixture by name."""
    fixtures = {
        "wikipedia_summary": WIKIPEDIA_SUMMARY,
        "wikipedia_search": WIKIPEDIA_SEARCH,
        "gdelt": GDELT_RESPONSE,
        "sec_tickers": SEC_COMPANY_TICKERS,
        "sec_submissions": SEC_SUBMISSIONS,
    }
    return fixtures.get(name, {})


def save_fixture(name: str, data: dict[str, Any]) -> None:
    """Save a fixture to disk."""
    path = FIXTURES_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))


def load_fixture(name: str) -> dict[str, Any]:
    """Load a fixture from disk."""
    path = FIXTURES_DIR / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    return get_fixture(name)
