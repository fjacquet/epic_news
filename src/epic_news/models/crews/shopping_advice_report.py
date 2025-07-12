"""Pydantic models for shopping advice output."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

__all__ = ["ShoppingAdviceOutput", "ProductInfo", "PriceInfo", "CompetitorInfo"]


class PriceInfo(BaseModel):
    """Price information for a product from a specific retailer."""

    retailer: str = Field(..., description="Name of the retailer")
    price: str = Field(..., description="Price with currency")
    url: Optional[str] = Field(None, description="Direct purchase link")
    shipping_cost: Optional[str] = Field(None, description="Shipping cost if available")
    total_cost: Optional[str] = Field(None, description="Total cost including shipping and taxes")
    notes: Optional[str] = Field(None, description="Additional notes about the offer")


class CompetitorInfo(BaseModel):
    """Information about a competing product."""

    name: str = Field(..., description="Name of the competing product")
    price_range: str = Field(..., description="Price range for this competitor")
    key_features: list[str] = Field(..., description="Key features of this competitor")
    pros: list[str] = Field(..., description="Advantages of this competitor")
    cons: list[str] = Field(..., description="Disadvantages of this competitor")
    target_audience: str = Field(..., description="Target audience for this competitor")


class ProductInfo(BaseModel):
    """Detailed product information."""

    name: str = Field(..., description="Product name")
    overview: str = Field(..., description="Product overview and description")
    key_specifications: list[str] = Field(..., description="Key technical specifications")
    pros: list[str] = Field(..., description="Product advantages")
    cons: list[str] = Field(..., description="Product disadvantages")
    target_audience: str = Field(..., description="Target audience and best use cases")
    common_issues: list[str] = Field(default_factory=list, description="Common issues and solutions")


class ShoppingAdviceOutput(BaseModel):
    """Schema for shopping advice output containing all research and analysis."""

    product_info: ProductInfo = Field(..., description="Detailed product information")
    switzerland_prices: list[PriceInfo] = Field(..., description="Prices from Swiss retailers")
    france_prices: list[PriceInfo] = Field(..., description="Prices from French retailers")
    competitors: list[CompetitorInfo] = Field(..., description="Competitor analysis")
    executive_summary: str = Field(..., description="Executive summary with clear recommendations")
    final_recommendations: str = Field(..., description="Final recommendations with reasoning")
    best_deals: list[str] = Field(..., description="Best deals and purchase recommendations")
    user_preferences_context: str = Field(..., description="User preferences and constraints considered")
