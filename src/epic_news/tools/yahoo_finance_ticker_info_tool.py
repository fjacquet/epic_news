"""
Tool for fetching Yahoo Finance Ticker Information.
"""
import json

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.finance_models import GetTickerInfoInput
from src.epic_news.tools.cache_manager import get_cache_manager


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
        cache = get_cache_manager()
        cache_key = f"yahoo_ticker_info_{ticker}"

        # Try to get from cache first (cache for 30 minutes)
        cached_result = cache.get(cache_key, ttl=1800)
        if cached_result is not None:
            return cached_result

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
            json_result = json.dumps(final_result)

            # Cache the result
            cache.set(cache_key, json_result)

            return json_result
        except Exception as e:
            error_msg = f"Error fetching ticker info for {ticker}: {str(e)}"
            return json.dumps({"error": error_msg, "ticker": ticker})
