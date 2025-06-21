"""Pydantic models for CoinMarketCap tools."""
from pydantic import BaseModel, Field


class CoinInfoInput(BaseModel):
    """Input schema for CoinMarketCapInfoTool."""
    symbol: str = Field(
        ..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)"
    )
