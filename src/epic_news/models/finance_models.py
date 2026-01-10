"""Pydantic models for finance tools."""


from pydantic import BaseModel, Field


class ExchangeRateToolInput(BaseModel):
    """Input for ExchangeRateTool."""

    base_currency: str | None = Field(
        default="USD",
        description="The base currency (3-letter ISO code) for exchange rates. Defaults to USD.",
    )
    target_currencies: list[str] | None = Field(
        default=None,
        description="A list of target currencies (3-letter ISO codes) to fetch. If None, all available rates for the base currency are returned.",
    )


class GetCompanyInfoInput(BaseModel):
    """Input schema for getting company information."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'MSFT').")


class GetETFHoldingsInput(BaseModel):
    """Input schema for getting ETF holdings."""

    ticker: str = Field(..., description="The ETF ticker symbol (e.g., 'VTI', 'SPY').")


class GetTickerHistoryInput(BaseModel):
    """Input schema for getting ticker price history."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')")
    period: str = Field("1y", description="Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max")
    interval: str = Field(
        "1d",
        description="Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo",
    )


class GetTickerNewsInput(BaseModel):
    """Input schema for getting news for a ticker."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'BTC-USD').")
    limit: int = Field(5, description="Maximum number of news items to return.")


class GetTickerInfoInput(BaseModel):
    """Input schema for getting ticker information."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')")


class KrakenTickerInfoInput(BaseModel):
    """Input schema for the KrakenTickerInfoTool."""

    pair: str = Field(
        ..., description="The cryptocurrency pair to get ticker information for (e.g., 'XXBTZUSD')."
    )


class KrakenAssetListInput(BaseModel):
    """Input schema for the KrakenAssetListTool."""

    asset_class: str = Field(default="currency", description="Asset class (e.g., 'currency').")
