"""
CoinMarketCap API Tools Loader.

This module provides a utility function to get all CoinMarketCap tools,
which are now defined in their respective separate files.
"""

from crewai.tools import BaseTool

# Import tool classes from their new locations
from .coinmarketcap_info_tool import CoinMarketCapInfoTool
from .coinmarketcap_list_tool import CoinMarketCapListTool
from .coinmarketcap_historical_tool import CoinMarketCapHistoricalTool
from .coinmarketcap_news_tool import CoinMarketCapNewsTool


def get_coinmarketcap_tools() -> list[BaseTool]:
    """
    Get a list of all CoinMarketCap tools.

    Returns:
        A list of CoinMarketCap tool instances.
    """
    return [
        CoinMarketCapInfoTool(),
        CoinMarketCapListTool(),
        CoinMarketCapHistoricalTool(),
        CoinMarketCapNewsTool(),
    ]
