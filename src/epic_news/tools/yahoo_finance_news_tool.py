"""
Tool for fetching Yahoo Finance News.
"""
import datetime
import json

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.finance_models import GetTickerNewsInput
from src.epic_news.tools.cache_manager import get_cache_manager


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
        cache = get_cache_manager()
        cache_key = f"yahoo_news_{ticker}_{limit}"

        # Try to get from cache first (cache for 15 minutes for news)
        cached_result = cache.get(cache_key, ttl=900)
        if cached_result is not None:
            return cached_result

        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news

            if not news:
                result = json.dumps({"message": f"No recent news found for {ticker}."})
                cache.set(cache_key, result)
                return result

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
            result = json.dumps({"ticker": ticker, "news": news_list})
            cache.set(cache_key, result)
            return result
        except Exception as e:
            result = json.dumps({"error": f"Error retrieving news for {ticker}: {str(e)}"})
            cache.set(cache_key, result)
            return result
