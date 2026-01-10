"""Pydantic models for CoinMarketCap tools."""

from pydantic import BaseModel, Field


class CoinInfoInput(BaseModel):
    """Input schema for CoinMarketCapInfoTool."""

    symbol: str = Field(..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)")


class CryptocurrencyHistoricalInput(BaseModel):
    """Input schema for CoinMarketCapHistoricalTool."""

    symbol: str = Field(..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)")
    time_period: str = Field(
        "30d",
        description="Time period for historical data: '24h', '7d', '30d', '3m', '1y', or 'ytd'",
    )


class CryptocurrencyListInput(BaseModel):
    """Input schema for CoinMarketCapListTool."""

    limit: int = Field(25, description="Number of cryptocurrencies to return (default: 25, max: 100)")
    sort: str = Field(
        "market_cap",
        description="Sort cryptocurrencies by: 'market_cap', 'volume_24h', 'price', or 'percent_change_24h'",
    )


class CryptocurrencyNewsInput(BaseModel):
    """Input schema for CoinMarketCapNewsTool."""

    symbol: str | None = Field(
        None,
        description="Cryptocurrency symbol (e.g., BTC) or slug (e.g., bitcoin) to get news for (optional)",
    )
    limit: int = Field(10, description="Number of news articles to return (default: 10, max: 50 for news)")


# class CoinInfoInput(BaseModel):
#     """Input schema for CoinMarketCapInfoTool."""
#     symbol: str = Field(
#         ..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)"
#     )
