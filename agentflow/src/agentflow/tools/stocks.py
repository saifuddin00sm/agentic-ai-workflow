"""Stock market tool using yfinance."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from agentflow.tools import ToolResult, Tool


class StockInput(BaseModel):
    """Input for stock tool."""

    ticker: str = Field(description="Stock ticker symbol, e.g. 'AAPL'")
    info_type: str = Field(
        default="overview",
        pattern="^(overview|price|history)$",
        description="Type of info: overview, price, or history",
    )


class StockTool(Tool[StockInput]):
    """Stock market data tool using yfinance."""

    name = "stocks"
    description = "Get stock market data: company overview, current price, or 1-year price history. Uses Yahoo Finance."
    input_model = StockInput

    async def run(self, input: StockInput) -> ToolResult:  # noqa: A002
        try:
            # Run yfinance in executor since it's sync
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._fetch_data, input)
            return result
        except Exception as e:
            return ToolResult(
                content=f"Stock data error: {type(e).__name__}: {str(e)[:300]}",
                is_error=True,
            )

    def _fetch_data(self, input: StockInput) -> ToolResult:  # noqa: A002
        import yfinance as yf  # type: ignore[import-untyped]

        ticker = yf.Ticker(input.ticker)

        if input.info_type == "overview":
            info: dict[str, Any] = ticker.info or {}
            lines = [
                f"Company: {info.get('longName', input.ticker)}",
                f"Sector: {info.get('sector', 'N/A')}",
                f"Industry: {info.get('industry', 'N/A')}",
                f"Market Cap: ${info.get('marketCap', 0):,.0f}",
                f"Employees: {info.get('fullTimeEmployees', 'N/A')}",
                f"Country: {info.get('country', 'N/A')}",
                f"Website: {info.get('website', 'N/A')}",
                f"Summary: {info.get('longBusinessSummary', 'N/A')[:500]}",
            ]
            return ToolResult(content="\n".join(lines))

        elif input.info_type == "price":
            info = ticker.info or {}
            hist = ticker.history(period="5d")
            lines = [
                f"Ticker: {input.ticker}",
                f"Current Price: ${info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}",
                f"Previous Close: ${info.get('previousClose', 'N/A')}",
                f"52-Week Range: ${info.get('fiftyTwoWeekLow', 'N/A')} - ${info.get('fiftyTwoWeekHigh', 'N/A')}",
                f"Volume: {info.get('volume', 'N/A')}",
            ]
            if not hist.empty:
                lines.append(f"\nRecent prices:")
                for date, row in hist.tail(5).iterrows():
                    lines.append(f"  {date.strftime('%Y-%m-%d')}: ${row['Close']:.2f}")
            return ToolResult(content="\n".join(lines))

        elif input.info_type == "history":
            hist = ticker.history(period="1y")
            if hist.empty:
                return ToolResult(content=f"No price history for {input.ticker}")

            lines = [f"1-Year Price History for {input.ticker}:"]
            # Sample monthly
            monthly = hist.resample("ME").last()
            for date, row in monthly.iterrows():
                lines.append(f"  {date.strftime('%Y-%m')}: ${row['Close']:.2f}")

            # Calculate performance
            if len(hist) > 1:
                start_price = hist.iloc[0]["Close"]
                end_price = hist.iloc[-1]["Close"]
                pct_change = ((end_price - start_price) / start_price) * 100
                lines.append(f"\n1Y Performance: {pct_change:+.1f}%")
                lines.append(f"Start: ${start_price:.2f} → End: ${end_price:.2f}")

            return ToolResult(content="\n".join(lines))

        return ToolResult(content="Unknown info_type", is_error=True)
