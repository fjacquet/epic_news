"""
Tool for fetching Yahoo Finance News.
"""
import datetime

import yfinance as yf
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GetTickerNewsInput(BaseModel):
    """Input schema for getting news for a ticker."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'BTC-USD').")
    limit: int = Field(5, description="Maximum number of news items to return.")


class YahooFinanceNewsTool(BaseTool):
    """
    Get recent news for a financial instrument from Yahoo Finance.

    This tool retrieves recent news articles related to a specific stock,
    ETF, or cryptocurrency ticker symbol.
    """

    name: str = "Yahoo Finance News Tool"
    description: str = (
        "Get recent news articles for stocks, ETFs, or cryptocurrencies, "
        "including headlines, publishers, and links to full articles."
    )
    args_schema: type[BaseModel] = GetTickerNewsInput

    def _run(self, ticker: str, limit: int = 5) -> str:
        """Execute the Yahoo Finance news lookup."""
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news

            if not news:
                return json.dumps({"message": f"No recent news found for {ticker}."})

            # Limit the number of news items
            news = news[:limit]

            # Format the news items
            news_list = []
            for item in news:
                published_timestamp = item.get("providerPublishTime")
                published_str = (
                    datetime.datetime.fromtimestamp(published_timestamp).strftime("%Y-%m-%d %H:%M")
                    if published_timestamp
                    else "Unknown date"
                )
                news_list.append({
                    "title": item.get("title") or "No title",
                    "publisher": item.get("publisher") or "Unknown publisher",
                    "link": item.get("link") or "#",
                    "published_date": published_str,
                })
            return json.dumps({"ticker": ticker, "news": news_list})
        except Exception as e:
            return json.dumps({"error": f"Error retrieving news for {ticker}: {str(e)}"})
