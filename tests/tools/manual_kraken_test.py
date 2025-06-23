#!/usr/bin/env python3
"""Test script for Kraken API connection and asset listing.

This script tests the connection to the Kraken API and lists the user's assets
(name and quantity) using the KrakenAssetListTool.
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from src.epic_news.tools.kraken_api_tool import KrakenAssetListTool, KrakenTickerInfoTool


def test_ticker_info(pair: str = "XXBTZUSD") -> None:
    """
    Test the connection to Kraken API by fetching ticker information.

    Args:
        pair: The cryptocurrency pair to get ticker information for.
    """
    print(f"Testing Kraken API connection by fetching ticker info for {pair}...")

    tool = KrakenTickerInfoTool()
    result = tool._run(pair=pair)

    try:
        # Try to parse the result as JSON to verify it's valid
        ticker_data = json.loads(result)
        print("✅ Connection successful! Sample ticker data:")
        print(json.dumps(ticker_data, indent=2)[:500] + "..." if len(result) > 500 else "")
        return True
    except json.JSONDecodeError:
        # If it's not valid JSON, it's probably an error message
        print(f"❌ Connection failed: {result}")
        return False


def list_assets(api_key: str, api_secret: str) -> list[dict[str, str | float]] | None:
    """
    List assets in the Kraken account.

    Args:
        api_key: Your Kraken API key.
        api_secret: Your Kraken API secret.

    Returns:
        A list of assets with their quantities if successful, None otherwise.
    """
    print("Fetching asset list from Kraken...")

    tool = KrakenAssetListTool()
    result = tool._run(api_key=api_key, api_secret=api_secret)

    try:
        # Try to parse the result as JSON
        assets = json.loads(result)

        if isinstance(assets, list):
            print(f"✅ Successfully retrieved {len(assets)} assets:")
            for asset in assets:
                print(f"  • {asset['asset']}: {asset['quantity']}")
            return assets
        print(f"❌ Error: Unexpected response format: {result}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: {result}")
        return None


def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test Kraken API connection and list assets.")
    parser.add_argument("--api-key", help="Your Kraken API key (overrides env var)")
    parser.add_argument("--api-secret", help="Your Kraken API secret (overrides env var)")
    parser.add_argument(
        "--pair", default="XXBTZUSD", help="Cryptocurrency pair for ticker test (default: XXBTZUSD)"
    )

    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    # Get API credentials from environment variables or command line arguments
    api_key = args.api_key or os.environ.get("KRAKEN_API_KEY")
    api_secret = args.api_secret or os.environ.get("KRAKEN_API_SECRET")

    # First test the connection using the public API (no auth required)
    connection_ok = test_ticker_info(args.pair)
    print("\n" + "-" * 50 + "\n")

    if not connection_ok:
        print("❌ Skipping asset listing due to connection failure.")
        sys.exit(1)

    # If API credentials are available, test asset listing
    if api_key and api_secret:
        assets = list_assets(api_key, api_secret)
        if not assets:
            sys.exit(1)
    else:
        print("❌ API credentials not found. Please set KRAKEN_API_KEY and KRAKEN_API_SECRET")
        print("in your .env file or provide them as command line arguments.")
        print("\nExample .env entry:")
        print("KRAKEN_API_KEY=your_api_key_here")
        print("KRAKEN_API_SECRET=your_api_secret_here")


if __name__ == "__main__":
    main()
