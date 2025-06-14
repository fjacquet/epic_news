"""
CoinMarketCap API tool for cryptocurrency detailed information.
"""

import os
import requests
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Assuming epic_news.tools.logger is accessible. If not, adjust or remove.
# from epic_news.tools.logger import get_logger
# logger = get_logger(__name__)
# For now, using standard logging if epic_news.tools.logger is an issue for standalone tool
import logging
logger = logging.getLogger(__name__)


# Base URL for CoinMarketCap API
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


class CoinMarketCapException(Exception):
    """Exception raised for CoinMarketCap API errors."""
    pass


class CoinInfoInput(BaseModel):
    """Input schema for CoinMarketCapInfoTool."""
    symbol: str = Field(
        ..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)"
    )


class CoinMarketCapInfoTool(BaseTool):
    """
    Tool for retrieving detailed information about a specific cryptocurrency.

    This tool provides current price, market cap, volume, circulating supply,
    and other key metrics for a given cryptocurrency symbol.
    """
    name: str = "CoinMarketCap Cryptocurrency Info"
    description: str = (
        "Get detailed information about a specific cryptocurrency including price, "
        "market cap, volume, circulating supply, and other key metrics. "
        "Provide the cryptocurrency symbol (e.g., BTC, ETH, SOL)."
    )
    args_schema: type[BaseModel] = CoinInfoInput

    def _run(self, symbol: str) -> str:
        """
        Retrieve detailed information about a specific cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol/ticker (e.g., BTC, ETH)

        Returns:
            A JSON string containing detailed information about the cryptocurrency

        Raises:
            CoinMarketCapException: If the API request fails
        """
        logger.info(f"Retrieving information for cryptocurrency: {symbol}")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }
            params = {"symbol": symbol.upper(), "convert": "USD"}
            response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/quotes/latest",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                error_msg = (
                    f"CoinMarketCap API error: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return json.dumps({"error": f"CoinMarketCap API error: {response.status_code} - {response.text}"})

            data = response.json()

            if "data" not in data or symbol.upper() not in data["data"]:
                logger.warning(f"No data found for symbol: {symbol}")
                return json.dumps({"error": f"No data found for cryptocurrency symbol: {symbol}"})

            crypto_data = data["data"][symbol.upper()]
            quote = crypto_data["quote"]["USD"]

            info_dict = {
                "name": crypto_data.get('name'),
                "symbol": crypto_data.get('symbol'),
                "price_usd": quote.get('price'),
                "market_cap_usd": quote.get('market_cap'),
                "volume_24h_usd": quote.get('volume_24h'),
                "percent_change_24h": quote.get('percent_change_24h'),
                "percent_change_7d": quote.get('percent_change_7d'),
                "circulating_supply": crypto_data.get('circulating_supply'),
                "max_supply": crypto_data.get('max_supply'),
                "cmc_rank": crypto_data.get('cmc_rank'),
                "last_updated": quote.get('last_updated'),
                "platform": crypto_data.get('platform', {}).get('name') if crypto_data.get('platform') else None,
                "tags": crypto_data.get('tags', [])[:5]
            }

            logger.info(f"Successfully retrieved information for {symbol}")
            return json.dumps(info_dict)

        except Exception as e:
            error_msg = f"Error retrieving cryptocurrency data for {symbol}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
