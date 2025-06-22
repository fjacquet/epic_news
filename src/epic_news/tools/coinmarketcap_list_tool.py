"""
CoinMarketCap API tool for listing top cryptocurrencies.
"""

import json

# Using standard logging
import logging
import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.coinmarketcap_models import CryptocurrencyListInput

logger = logging.getLogger(__name__)

# Base URL for CoinMarketCap API
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


class CoinMarketCapListTool(BaseTool):
    """
    Tool for retrieving a list of top cryptocurrencies.

    This tool provides a list of cryptocurrencies sorted by market cap,
    volume, or price with their current metrics.
    """
    name: str = "CoinMarketCap Cryptocurrency List"
    description: str = (
        "Get a list of top cryptocurrencies sorted by market cap, volume, price, "
        "or recent performance. Returns key metrics for each cryptocurrency."
    )
    args_schema: type[BaseModel] = CryptocurrencyListInput

    def _run(self, limit: int = 25, sort: str = "market_cap") -> str:
        """
        Retrieve a list of top cryptocurrencies.

        Args:
            limit: Number of cryptocurrencies to return (default: 25, max: 100)
            sort: Sort by 'market_cap', 'volume_24h', 'price', or 'percent_change_24h'

        Returns:
            A JSON string containing a list of top cryptocurrencies with their metrics

        Raises:
            CoinMarketCapException: If the API request fails
        """
        logger.info(f"Retrieving top {limit} cryptocurrencies sorted by {sort}")

        # Validate and cap limit
        if limit > 100:
            limit = 100
            logger.warning("Limit capped at 100 cryptocurrencies")

        # Map sort parameter to API sort parameter
        sort_map = {
            "market_cap": "market_cap",
            "volume_24h": "volume_24h",
            "price": "price",
            "percent_change_24h": "percent_change_24h",
        }
        sort_by = sort_map.get(sort, "market_cap")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }
            params = {"limit": limit, "sort": sort_by, "convert": "USD"}

            response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/listings/latest",
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

            if "data" not in data:
                logger.warning("No cryptocurrency data found")
                return json.dumps({"error": "No cryptocurrency data found"})

            results_list = []
            for crypto in data["data"]:
                quote = crypto["quote"]["USD"]
                crypto_info = {
                    "rank": crypto.get('cmc_rank'),
                    "name": crypto.get('name'),
                    "symbol": crypto.get('symbol'),
                    "price_usd": quote.get('price'),
                    "percent_change_24h": quote.get('percent_change_24h'),
                    "market_cap_usd": quote.get('market_cap'),
                    "volume_24h_usd": quote.get('volume_24h')
                }
                results_list.append(crypto_info)
            
            logger.info(
                f"Successfully retrieved list of {len(results_list)} cryptocurrencies"
            )
            return json.dumps(results_list)

        except Exception as e:
            error_msg = f"Error retrieving cryptocurrency list: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
