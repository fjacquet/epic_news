#!/usr/bin/env python3
"""
Knowledge Base Update Tool for epic_news.

This script provides functionality to periodically update the RAG knowledge base
with fresh financial data and prune outdated information.
"""

import datetime

import yfinance as yf
from crewai_tools import RagTool
from loguru import logger

from epic_news.rag_config import DEFAULT_RAG_CONFIG
from epic_news.tools.save_to_rag_tool import SaveToRagTool

# Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)


def update_market_data(tickers: list[str], collection_suffix: str | None = None) -> None:
    """
    Update the knowledge base with fresh market data for specified tickers.

    Args:
        tickers: List of ticker symbols to update
        collection_suffix: Optional suffix for the collection name
    """
    # Create RAG tools with the appropriate collection
    config = DEFAULT_RAG_CONFIG.copy()
    if collection_suffix:
        config["vectordb"]["config"] = config["vectordb"]["config"].copy()
        config["vectordb"]["config"]["collection_name"] = f"epic_news-{collection_suffix}"

    rag_tool = RagTool(config=config, summarize=True)
    save_tool = SaveToRagTool(rag_tool=rag_tool)

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    for ticker in tickers:
        try:
            # Get latest data
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            # Format key information
            if "shortName" in info:
                name = info.get("shortName", ticker)
                sector = info.get("sector", "Unknown")
                industry = info.get("industry", "Unknown")
                market_cap = info.get("marketCap", "Unknown")
                current_price = info.get("currentPrice", info.get("regularMarketPrice", "Unknown"))

                # Format financial metrics
                pe_ratio = info.get("trailingPE", "Unknown")
                dividend_yield = info.get("dividendYield", "Unknown")
                if dividend_yield != "Unknown":
                    dividend_yield = f"{float(dividend_yield) * 100:.2f}%"

                # Create knowledge entry
                entry = f"""
                Market Data Update for {name} ({ticker}) - {current_date}

                Current Price: {current_price}
                Market Cap: {market_cap}
                Sector: {sector}
                Industry: {industry}
                P/E Ratio: {pe_ratio}
                Dividend Yield: {dividend_yield}

                This data was automatically collected and added to the knowledge base
                as part of the periodic update process.
                """

                # Store in knowledge base
                save_tool._run(entry)
                logger.info(f"Updated knowledge base with data for {ticker}")

            else:
                logger.warning(f"Could not retrieve complete information for {ticker}")

        except Exception as e:
            logger.error(f"Error updating {ticker}: {str(e)}")


def prune_outdated_knowledge(max_age_days: int = 30, collection_suffix: str | None = None) -> None:
    """
    Remove outdated entries from the knowledge base.

    Args:
        max_age_days: Maximum age of entries to keep (in days)
        collection_suffix: Optional suffix for the collection name
    """
    # This is a placeholder for future implementation
    # Currently, ChromaDB doesn't have a simple way to delete documents by metadata
    # This would require custom implementation with the ChromaDB API
    logger.info(f"Pruning outdated knowledge (older than {max_age_days} days) is not yet implemented")
    logger.info("This feature will be implemented in a future version")


def main():
    """Main entry point for the knowledge base update script."""
    # Example usage
    logger.info("Starting knowledge base update")

    # Update stock data
    stock_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    update_market_data(stock_tickers, collection_suffix="stock")

    # Update ETF data
    etf_tickers = ["SPY", "QQQ", "VTI", "ARKK", "XLF"]
    update_market_data(etf_tickers, collection_suffix="etf")

    # Update crypto data (using Yahoo Finance format)
    crypto_tickers = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOT-USD"]
    update_market_data(crypto_tickers, collection_suffix="crypto")

    # Prune outdated knowledge
    prune_outdated_knowledge(max_age_days=30)

    logger.info("Knowledge base update completed")


if __name__ == "__main__":
    main()
