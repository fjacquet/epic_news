"""
CoinMarketCap API Tools Loader.

This module provides a utility function to get all CoinMarketCap tools,
which are now defined in their respective separate files.
"""

from crewai.tools import BaseTool
from crewai_custom_tools import (
    CoinMarketCapHistoricalTool,
    CoinMarketCapInfoTool,
    CoinMarketCapListTool,
    CoinMarketCapNewsTool,
)


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
