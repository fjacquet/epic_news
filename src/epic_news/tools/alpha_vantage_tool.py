"""
Alpha Vantage API Tools for epic_news.

This module provides tools to interact with the Alpha Vantage API for fetching
comprehensive financial data, including fundamental data, technical indicators,
and more.
"""

import json
import os
from typing import Type

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel

from src.epic_news.models.alpha_vantage_models import CompanyOverviewInput

load_dotenv()


class AlphaVantageCompanyOverviewTool(BaseTool):
    """
    A tool to fetch company overview and fundamental data from Alpha Vantage.

    This tool uses the Alpha Vantage API to retrieve key financial metrics
    and company information for a given stock ticker. It requires an
    ALPHA_VANTAGE_API_KEY to be set in the environment variables.
    """

    name: str = "Alpha Vantage Company Overview"
    description: str = (
        "Fetches fundamental data and a company overview for a specific stock ticker "
        "from Alpha Vantage. Use this to get detailed financial metrics like Market Cap, "
        "P/E Ratio, EPS, and more."
    )
    args_schema: Type[BaseModel] = CompanyOverviewInput

    def _run(self, ticker: str) -> str:
        """Execute the tool to fetch company overview data."""
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return "Error: ALPHA_VANTAGE_API_KEY environment variable not set."

        url = (
            f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}"
            f"&apikey={api_key}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            if not data or "Note" in data:
                return f"No data found for ticker {ticker}. It might be an invalid symbol."

            # Filter out metadata and return a clean JSON string of the overview
            return json.dumps(data, indent=2)

        except requests.exceptions.RequestException as e:
            return f"Error fetching data from Alpha Vantage: {e}"
        except json.JSONDecodeError:
            return "Error: Failed to parse JSON response from Alpha Vantage."
