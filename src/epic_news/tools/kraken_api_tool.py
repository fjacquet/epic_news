"""
Kraken API Tools for epic_news.

This module provides tools for interacting with the Kraken cryptocurrency exchange API.
It allows for fetching market data like ticker information, order books, and historical data,
as well as account-specific information like asset balances.
"""


import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
from typing import Dict, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.finance_models import KrakenAssetListInput, KrakenTickerInfoInput


class KrakenTickerInfoTool(BaseTool):
    """
    A tool to fetch real-time ticker information from Kraken.

    This tool queries the Kraken API for the latest price data for a given
    cryptocurrency pair, including ask, bid, last trade, volume, and more.
    """

    name: str = "Kraken Ticker Information"
    description: str = "Fetches real-time ticker information for a specific cryptocurrency pair from Kraken."
    args_schema: Type[BaseModel] = KrakenTickerInfoInput

    def _run(self, pair: str) -> str:
        """Execute the tool to fetch ticker data."""
        url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                return f"Error from Kraken API: {data['error']}"

            # The actual ticker data is nested under the pair name in the result
            result_pair = list(data.get("result", {}).keys())
            if not result_pair:
                return f"No data found for pair {pair}. It may be an invalid pair."

            ticker_data = data["result"][result_pair[0]]
            return json.dumps(ticker_data, indent=2)

        except requests.exceptions.RequestException as e:
            return f"Error fetching data from Kraken: {e}"
        except json.JSONDecodeError:
            return "Error: Failed to parse JSON response from Kraken."


class KrakenAssetListTool(BaseTool):
    """
    A tool to fetch account assets from Kraken.

    This tool queries the Kraken API for the current asset balances in your account,
    including the asset name and quantity.
    """

    name: str = "Kraken Asset List"
    description: str = "Fetches your account's asset balances from Kraken, including asset names and quantities."
    args_schema: Type[BaseModel] = KrakenAssetListInput

    def _get_kraken_signature(self, urlpath: str, data: Dict, secret: str) -> str:
        """
        Create authentication signature for Kraken API private endpoints.
        """
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        
        signature = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())
        
        return sigdigest.decode()

    def _run(self, asset_class: str = "currency") -> str:
        """
        Execute the tool to fetch asset balances.
        """
        # Kraken API endpoint for account balance
        url = "https://api.kraken.com/0/private/Balance"
        urlpath = "/0/private/Balance"
        
        # Prepare request data
        data = {
            "nonce": str(int(time.time() * 1000)),
            "asset": asset_class
        }
        
        # Get API credentials from environment variables
        api_key = os.environ.get('KRAKEN_API_KEY')
        api_secret = os.environ.get('KRAKEN_API_SECRET')
        
        if not api_key or not api_secret:
            return "Error: Kraken API credentials not found in environment variables."
        
        # Prepare headers with API key and signature
        headers = {
            'API-Key': api_key,
            'API-Sign': self._get_kraken_signature(urlpath, data, api_secret)
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("error") and result["error"]:
                return f"Error from Kraken API: {result['error']}"
            
            # Format the asset data for better readability
            assets = result.get("result", {})
            formatted_assets = []
            
            for asset_code, quantity in assets.items():
                # Convert quantity to float for better formatting
                try:
                    qty = float(quantity)
                    # Skip assets with zero balance
                    if qty <= 0:
                        continue
                    formatted_assets.append({
                        "asset": asset_code,
                        "quantity": qty
                    })
                except (ValueError, TypeError):
                    formatted_assets.append({
                        "asset": asset_code,
                        "quantity": quantity  # Keep as string if conversion fails
                    })
            
            return json.dumps(formatted_assets, indent=2)
        
        except Exception as e:
            return f"Error fetching asset balances: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Failed to parse JSON response from Kraken."
