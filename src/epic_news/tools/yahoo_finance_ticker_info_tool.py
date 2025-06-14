"""
Tool for fetching Yahoo Finance Ticker Information.
"""
import yfinance as yf
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GetTickerInfoInput(BaseModel):
    """Input schema for getting ticker information."""

    ticker: str = Field(
        ..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')"
    )


class YahooFinanceTickerInfoTool(BaseTool):
    """
    Get basic information about a financial instrument from Yahoo Finance.

    This tool retrieves key data points about a stock, ETF, or cryptocurrency
    including current price, market cap, 52-week range, and more.
    """

    name: str = "Yahoo Finance Ticker Info Tool"
    description: str = (
        "Get current information about stocks, ETFs, or cryptocurrencies including price,"
        " market cap, P/E ratio, volume, and other key stats."
    )
    args_schema: type[BaseModel] = GetTickerInfoInput

    def _run(self, ticker: str) -> str:
        """Execute the Yahoo Finance ticker info lookup."""
        try:
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info

            # Format a clean subset of the most important information
            result = {
                "symbol": ticker,
                "name": info.get("shortName", "N/A"),
                "currency": info.get("currency", "N/A"),
                "current_price": info.get(
                    "currentPrice", info.get("regularMarketPrice", "N/A")
                ),
                "previous_close": info.get("previousClose", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "volume": info.get("volume", "N/A"),
                "average_volume": info.get("averageVolume", "N/A"),
                "52wk_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52wk_low": info.get("fiftyTwoWeekLow", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
            }

            # Remove N/A values for cleaner output
            final_result = {k: v for k, v in result.items() if v != "N/A"}
            return json.dumps(final_result)
        except Exception as e:
            return json.dumps({"error": f"Failed to get ticker info for {ticker}: {str(e)}"})
