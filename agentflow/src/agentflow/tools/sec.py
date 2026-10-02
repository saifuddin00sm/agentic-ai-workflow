"""SEC EDGAR filings tool."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentflow.tools import ToolResult, Tool, http_get


class SecInput(BaseModel):
    """Input for SEC filings tool."""

    company: str = Field(description="Company name or ticker to search")
    filing_type: str = Field(
        default="all",
        description="Filing type: 10-K, 10-Q, 8-K, or 'all'",
    )
    max_results: int = Field(default=10, ge=1, le=20)


class SecFilingsTool(Tool[SecInput]):
    """SEC EDGAR submissions API tool."""

    name = "sec_filings"
    description = "Search SEC EDGAR for company filings (10-K, 10-Q, 8-K). Returns recent filing metadata. No API key required."
    input_model = SecInput

    async def run(self, input: SecInput) -> ToolResult:  # noqa: A002
        # First, try to find the CIK for the company
        cik = await self._find_cik(input.company)
        if not cik:
            return ToolResult(
                content=f"Could not find SEC registrant for: {input.company}",
                is_error=True,
            )

        # Get recent filings
        return await self._get_filings(cik, input.filing_type, input.max_results)

    async def _find_cik(self, company: str) -> str | None:
        """Look up CIK from company name/ticker."""
        # Try ticker lookup first (common tickers)
        resp = await http_get(
            "https://www.sec.gov/cgi-bin/browse-edgar",
            params={"company": company, "action": "getcompany", "output": "atom"},
        )

        # Alternative: use the EDGAR company search
        resp = await http_get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": company, "dateRange": "custom&startdt=2020-01-01"},
        )

        # Use the company tickers JSON
        resp = await http_get("https://www.sec.gov/files/company_tickers.json")
        if resp.status_code == 200:
            data = resp.json()
            company_lower = company.lower()
            for _key, entry in data.items():
                if (
                    entry.get("ticker", "").lower() == company_lower
                    or company_lower in entry.get("title", "").lower()
                ):
                    return str(entry["cik_str"]).zfill(10)

        return None

    async def _get_filings(
        self, cik: str, filing_type: str, max_results: int
    ) -> ToolResult:
        """Get recent filings for a CIK."""
        resp = await http_get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
        )

        if resp.status_code != 200:
            return ToolResult(
                content=f"SEC API returned status {resp.status_code} for CIK {cik}",
                is_error=True,
            )

        data = resp.json()
        company_name = data.get("name", "Unknown")
        recent = data.get("filings", {}).get("recent", {})

        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocument", [])

        if not forms:
            return ToolResult(content=f"No filings found for {company_name} (CIK: {cik})")

        # Filter by type if specified
        entries = list(zip(forms, dates, accessions, descriptions))
        if filing_type != "all":
            entries = [e for e in entries if e[0] == filing_type]

        entries = entries[:max_results]

        lines = [f"SEC Filings for {company_name} (CIK: {cik}):\n"]
        for form, date, accession, doc in entries:
            acc_clean = accession.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_clean}/{doc}"
            lines.append(f"- [{form}] {date}: {doc}")
            lines.append(f"  URL: {url}")

        return ToolResult(
            content="\n".join(lines),
            metadata={"company": company_name, "cik": cik, "filing_count": len(entries)},
        )
