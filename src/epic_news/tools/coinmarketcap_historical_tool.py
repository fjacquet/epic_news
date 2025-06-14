"""
CoinMarketCap API tool for cryptocurrency historical data.
"""

import os
import requests
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Using standard logging
import logging
logger = logging.getLogger(__name__)

# Base URL for CoinMarketCap API
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


class CoinMarketCapException(Exception):
    """Exception raised for CoinMarketCap API errors."""
    pass


class CryptocurrencyHistoricalInput(BaseModel):
    """Input schema for CoinMarketCapHistoricalTool."""
    symbol: str = Field(
        ..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)"
    )
    time_period: str = Field(
        "30d",
        description="Time period for historical data: '24h', '7d', '30d', '3m', '1y', or 'ytd'",
    )


class CoinMarketCapHistoricalTool(BaseTool):
    """
    Tool for retrieving historical price data for a specific cryptocurrency.

    This tool provides historical price, volume, and market cap data for
    a given cryptocurrency over various time periods.
    """
    name: str = "CoinMarketCap Historical Data"
    description: str = (
        "Get historical price, volume, and market cap data for a specific cryptocurrency "
        "over various time periods (24h, 7d, 30d, 3m, 1y, or ytd)."
    )
    args_schema: type[BaseModel] = CryptocurrencyHistoricalInput

    def _run(self, symbol: str, time_period: str = "30d") -> str:
        """
        Retrieve historical data for a specific cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol/ticker (e.g., BTC, ETH)
            time_period: Time period for historical data

        Returns:
            A JSON string containing historical data for the cryptocurrency

        Raises:
            CoinMarketCapException: If the API request fails
        """
        logger.info(f"Retrieving {time_period} historical data for {symbol}")

        time_map = {
            "24h": "hourly", "7d": "daily", "30d": "daily",
            "3m": "daily", "1y": "weekly", "ytd": "daily",
        }
        interval = time_map.get(time_period, "daily")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }

            id_params = {"symbol": symbol.upper()}
            id_response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/map", headers=headers, params=id_params
            )

            if id_response.status_code != 200:
                error_msg = f"CoinMarketCap API error retrieving ID: {id_response.status_code} - {id_response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            id_data = id_response.json()
            if not id_data.get("data"):
                logger.warning(f"No ID found for symbol: {symbol}")
                return json.dumps({"error": f"No ID found for cryptocurrency symbol: {symbol}"})
            
            # Ensure 'data' is a list and has elements before accessing id_data["data"][0]
            if not isinstance(id_data["data"], list) or not id_data["data"]:
                 logger.warning(f"Unexpected ID data format for symbol: {symbol}. Data: {id_data}")
                 return json.dumps({"error": f"Unexpected ID data format for symbol: {symbol}"})

            crypto_id = id_data["data"][0]["id"]

            history_params = {
                "id": crypto_id, "convert": "USD",
                "interval": interval, "time_period": time_period,
            }
            history_response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/quotes/historical",
                headers=headers, params=history_params,
            )

            if history_response.status_code != 200:
                error_msg = f"CoinMarketCap API error retrieving historical data: {history_response.status_code} - {history_response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            history_data = history_response.json()
            if "data" not in history_data or "quotes" not in history_data["data"]:
                logger.warning(f"No historical data found for {symbol} over {time_period}")
                return json.dumps({"error": f"No historical data found for {symbol} over {time_period}"})

            quotes = history_data["data"]["quotes"]
            historical_data_list = []
            for quote_data in quotes:
                q_usd = quote_data["quote"]["USD"]
                entry = {
                    "timestamp": quote_data.get("timestamp"),
                    "price_usd": q_usd.get("price"),
                    "volume_24h_usd": q_usd.get("volume_24h"),
                    "market_cap_usd": q_usd.get("market_cap"),
                    # Historical API might not have percent_change_24h per entry,
                    # it's usually calculated based on previous point.
                    # Keeping it if API provides, otherwise might be None.
                    "percent_change_24h": q_usd.get("percent_change_24h")
                }
                historical_data_list.append(entry)

            result = {
                "symbol": symbol,
                "time_period": time_period,
                "interval": interval,
                "historical_data": historical_data_list
            }
            logger.info(f"Successfully retrieved historical data for {symbol}")
            return json.dumps(result)

        except Exception as e:
            error_msg = f"Error retrieving historical data for {symbol}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
