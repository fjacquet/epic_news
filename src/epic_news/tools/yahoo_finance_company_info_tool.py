"""
Tool for fetching Yahoo Finance Company Information.
"""
import json

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.finance_models import GetCompanyInfoInput


class YahooFinanceCompanyInfoTool(BaseTool):
    """
    Get detailed company information from Yahoo Finance.

    This tool retrieves comprehensive company data including business description,
    financial metrics, and key performance indicators.
    """

    name: str = "Yahoo Finance Company Info Tool"
    description: str = (
        "Get detailed company information including business description, "
        "key financial metrics, and company profile."
    )
    args_schema: type[BaseModel] = GetCompanyInfoInput

    def _run(self, ticker: str) -> str:
        """Execute the Yahoo Finance company info lookup."""
        try:
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info

            # Create a focused company profile
            company_info = {
                "symbol": ticker,
                "name": info.get("longName", "N/A"),
                "industry": info.get("industry", "N/A"),
                "sector": info.get("sector", "N/A"),
                "website": info.get("website", "N/A"),
                "country": info.get("country", "N/A"),
                "employees": info.get("fullTimeEmployees", "N/A"),
                "business_summary": info.get("longBusinessSummary", "N/A"),
                "financial_metrics": {
                    "revenue": info.get("totalRevenue", "N/A"),
                    "profit_margin": info.get("profitMargins", "N/A"),
                    "ebitda": info.get("ebitda", "N/A"),
                    "debt_to_equity": info.get("debtToEquity", "N/A"),
                    "return_on_equity": info.get("returnOnEquity", "N/A"),
                    "revenue_growth": info.get("revenueGrowth", "N/A"),
                    "earnings_growth": info.get("earningsGrowth", "N/A"),
                },
                "valuation_metrics": {
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "forward_pe": info.get("forwardPE", "N/A"),
                    "price_to_book": info.get("priceToBook", "N/A"),
                    "price_to_sales": info.get("priceToSalesTrailing12Months", "N/A"),
                },
            }

            # Clean up N/A values
            result = {
                k:
                v
                if not isinstance(v, dict)
                else {k2: v2 for k2, v2 in v.items() if v2 != "N/A"}
                for k, v in company_info.items()
                if v != "N/A"
            }
            # Additional cleanup for empty metric dicts
            if "financial_metrics" in result and not result["financial_metrics"]:
                del result["financial_metrics"]
            if "valuation_metrics" in result and not result["valuation_metrics"]:
                del result["valuation_metrics"]

            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": f"Failed to get company info for {ticker}: {str(e)}"})
