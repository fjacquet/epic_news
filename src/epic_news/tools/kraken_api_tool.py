"""
Kraken API Tools for epic_news.

This module provides tools for interacting with the Kraken cryptocurrency exchange API.
It allows for fetching market data like ticker information, order books, and historical data.
"""

import json
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TickerInfoInput(BaseModel):
    """Input schema for the KrakenTickerInfoTool."""

    pair: str = Field(..., description="The cryptocurrency pair to get ticker information for (e.g., 'XXBTZUSD').")


class KrakenTickerInfoTool(BaseTool):
    """
    A tool to fetch real-time ticker information from Kraken.

    This tool queries the Kraken API for the latest price data for a given
    cryptocurrency pair, including ask, bid, last trade, volume, and more.
    """

    name: str = "Kraken Ticker Information"
    description: str = "Fetches real-time ticker information for a specific cryptocurrency pair from Kraken."
    args_schema: Type[BaseModel] = TickerInfoInput

    def _run(self, pair: str) -> str:
        """Execute the tool to fetch ticker data."""
        url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                return f"Error from Kraken API: {data['error']}"

            # The actual ticker data is nested under the pair name in the result
            result_pair = list(data.get("result", {}).keys())
            if not result_pair:
                return f"No data found for pair {pair}. It may be an invalid pair."

            ticker_data = data["result"][result_pair[0]]
            return json.dumps(ticker_data, indent=2)

        except requests.exceptions.RequestException as e:
            return f"Error fetching data from Kraken: {e}"
        except json.JSONDecodeError:
            return "Error: Failed to parse JSON response from Kraken."
