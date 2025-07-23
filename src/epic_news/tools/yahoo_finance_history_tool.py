"""
Tool for fetching Yahoo Finance Ticker History.
"""

import json

import pandas as pd
import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel

from epic_news.models.finance_models import GetTickerHistoryInput


class YahooFinanceHistoryTool(BaseTool):
    """
    Get historical price data for a financial instrument from Yahoo Finance.

    This tool retrieves historical price data for stocks, ETFs, or cryptocurrencies
    over a specified time period and interval.
    """

    name: str = "Yahoo Finance History Tool"
    description: str = (
        "Get historical price data (open, high, low, close, volume) for stocks, ETFs,"
        " or cryptocurrencies over various time periods and intervals."
    )
    args_schema: type[BaseModel] = GetTickerHistoryInput

    def _run(self, ticker: str, period: str = "1y", interval: str = "1d") -> str:
        """Execute the Yahoo Finance historical data lookup."""
        try:
            ticker_data = yf.Ticker(ticker)
            history = ticker_data.history(period=period, interval=interval)

            if history.empty:
                return json.dumps({"error": f"No historical data available for {ticker}"})

            # Format the data for easier consumption
            history_list = []
            for date, row in history.iterrows():
                history_list.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "open": round(float(val) if not pd.isna(val := row.get("Open")) else 0.0, 2),
                        "high": round(float(val) if not pd.isna(val := row.get("High")) else 0.0, 2),
                        "low": round(float(val) if not pd.isna(val := row.get("Low")) else 0.0, 2),
                        "close": round(float(val) if not pd.isna(val := row.get("Close")) else 0.0, 2),
                        "volume": int(val) if not pd.isna(val := row.get("Volume")) else 0,
                    }
                )

            # Add summary statistics
            latest = history_list[-1] if history_list else {}
            earliest = history_list[0] if history_list else {}

            summary = {
                "symbol": ticker,
                "period": period,
                "interval": interval,
                "start_date": earliest.get("date", "N/A"),
                "end_date": latest.get("date", "N/A"),
                "price_change": round(latest.get("close", 0) - earliest.get("close", 0), 2),
                "price_change_percent": round(
                    (latest.get("close", 0) / (div if (div := earliest.get("close")) and div != 0 else 1) - 1)
                    * 100,
                    2,
                ),
                "data_points": len(history_list),
            }

            result = {
                "summary": summary,
                "history": history_list[-10:],  # Return only last 10 data points to avoid overloading
            }
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": f"Failed to get history for {ticker}: {str(e)}"})
