"""
Finance tool initialization module for epic_news crews.

This module provides convenient functions to initialize and register
financial data tools for use in epic_news crews.
"""

from crewai.tools import BaseTool

from epic_news.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from epic_news.tools.kraken_api_tool import KrakenTickerInfoTool
from epic_news.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool
from epic_news.tools.yahoo_finance_etf_holdings_tool import YahooFinanceETFHoldingsTool
from epic_news.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from epic_news.tools.yahoo_finance_news_tool import YahooFinanceNewsTool
from epic_news.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool


def get_yahoo_finance_tools() -> list[BaseTool]:
    """
    Initialize and return all Yahoo Finance tools.

    Returns:
        list[BaseTool]: A list of initialized Yahoo Finance tools ready for crew usage.

    """
    return [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceCompanyInfoTool(),
        YahooFinanceETFHoldingsTool(),
        YahooFinanceNewsTool(),
    ]


def get_stock_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for stock research.

    Returns:
        list[BaseTool]: A list of tools focused on stock analysis.

    """
    return [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceCompanyInfoTool(),
        YahooFinanceNewsTool(),
        AlphaVantageCompanyOverviewTool(),
    ]


def get_crypto_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for crypto research.

    Returns:
        list[BaseTool]: A list of tools focused on crypto analysis.

    """
    return [
        YahooFinanceHistoryTool(),
        YahooFinanceNewsTool(),
        YahooFinanceTickerInfoTool(),
        KrakenTickerInfoTool(),
    ]


def get_etf_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for ETF research.

    Returns:
        list[BaseTool]: A list of tools focused on ETF analysis.

    """
    return [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceETFHoldingsTool(),
        YahooFinanceNewsTool(),
    ]
