"""
Utilities for normalizing data before Pydantic validation.

This module provides functions to normalize data values to match expected enum values
in Pydantic models, particularly for the SalesProspectingReport model.
"""

from typing import Any


def normalize_metric_type(value: str) -> str:
    """
    Normalize metric type values to match the MetricType enum values.

    Args:
        value: The input metric type value to normalize

    Returns:
        A normalized string that matches one of the MetricType enum values
    """
    if value is None:
        return "numeric"  # Default to numeric if None

    value_lower = value.lower()

    # Direct match for enum values
    if value_lower in ["numeric", "percentage", "currency", "time", "count", "rating", "text"]:
        return value_lower

    # Mapping of input values to MetricType enum values
    mapping = {
        # Numeric types
        "quantitative": "numeric",
        "numerical": "numeric",
        "number": "numeric",
        "integer": "numeric",
        "float": "numeric",
        "decimal": "numeric",
        "value": "numeric",
        "metric": "numeric",
        "measurement": "numeric",
        "quantity": "numeric",
        # Percentage types
        "financial": "percentage",
        "percent": "percentage",
        "ratio": "percentage",
        "proportion": "percentage",
        "rate": "percentage",
        "fraction": "percentage",
        # Currency types
        "monetary": "currency",
        "money": "currency",
        "dollar": "currency",
        "euro": "currency",
        "cost": "currency",
        "price": "currency",
        "revenue": "currency",
        "sales": "currency",
        # Time types
        "temporal": "time",
        "duration": "time",
        "period": "time",
        "date": "time",
        "datetime": "time",
        "timestamp": "time",
        "interval": "time",
        # Count types
        "frequency": "count",
        "occurrence": "count",
        "instances": "count",
        "tally": "count",
        "total": "count",
        "sum": "count",
        # Rating types
        "score": "rating",
        "stars": "rating",
        "grade": "rating",
        "rank": "rating",
        "evaluation": "rating",
        "assessment": "rating",
        # Text types
        "string": "text",
        "qualitative": "text",
        "descriptive": "text",
        "verbal": "text",
        "narrative": "text",
        "comment": "text",
        "description": "text",
    }

    # Return the mapped value if found, otherwise default to "numeric" for safety
    return mapping.get(value_lower, "numeric")


def normalize_trend_direction(value: str) -> str:
    """
    Normalize trend direction values to match the TrendDirection enum values.

    Args:
        value: The input trend direction value to normalize

    Returns:
        A normalized string that matches one of the TrendDirection enum values
    """
    if value is None:
        return "unknown"

    value_lower = value.lower()

    # Direct match for enum values
    if value_lower in ["up", "down", "stable", "volatile", "unknown"]:
        return value_lower

    # Mapping of input values to TrendDirection enum values
    mapping = {
        # Up trend
        "upward": "up",
        "increasing": "up",
        "growing": "up",
        "positive": "up",  # This was missing in the error
        "rise": "up",
        "rising": "up",
        "improved": "up",
        "improving": "up",
        "higher": "up",
        "increase": "up",
        "growth": "up",
        "better": "up",
        "stronger": "up",
        "gain": "up",
        "gains": "up",
        "uptrend": "up",
        "bull": "up",
        "bullish": "up",
        # Down trend
        "downward": "down",
        "decreasing": "down",
        "declining": "down",
        "negative": "down",
        "fall": "down",
        "falling": "down",
        "deteriorating": "down",
        "lower": "down",
        "decrease": "down",
        "decline": "down",
        "worse": "down",
        "weaker": "down",
        "loss": "down",
        "losses": "down",
        "downtrend": "down",
        "bear": "down",
        "bearish": "down",
        # Stable trend
        "unchanged": "stable",
        "consistent": "stable",
        "flat": "stable",
        "steady": "stable",
        "constant": "stable",
        "maintained": "stable",
        "neutral": "stable",
        "balanced": "stable",
        "even": "stable",
        "level": "stable",
        "same": "stable",
        "equal": "stable",
        "stationary": "stable",
        # Volatile trend
        "fluctuating": "volatile",
        "unstable": "volatile",
        "erratic": "volatile",
        "variable": "volatile",
        "inconsistent": "volatile",
        "unpredictable": "volatile",
        "changing": "volatile",
        "swinging": "volatile",
        "oscillating": "volatile",
        "turbulent": "volatile",
        # Unknown trend
        "undetermined": "unknown",
        "unclear": "unknown",
        "not available": "unknown",
        "na": "unknown",
        "n/a": "unknown",
        "missing": "unknown",
        "no data": "unknown",
    }

    # Return the mapped value if found, otherwise default to "unknown" for safety
    return mapping.get(value_lower, "unknown")


def normalize_structured_data_report(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a StructuredDataReport dictionary to ensure all enum values match expected values.

    Args:
        data: The input data dictionary representing a StructuredDataReport

    Returns:
        A normalized dictionary with corrected enum values
    """
    if not data:
        return data

    # Normalize metrics
    if "metrics" in data and isinstance(data["metrics"], list):
        for metric in data["metrics"]:
            if "type" in metric:
                metric["type"] = normalize_metric_type(metric["type"])

            if "value" in metric and isinstance(metric["value"], dict) and "trend" in metric["value"]:
                metric["value"]["trend"] = normalize_trend_direction(metric["value"]["trend"])

    # Normalize KPIs
    if "kpis" in data and isinstance(data["kpis"], list):
        for kpi in data["kpis"]:
            if "type" in kpi:
                kpi["type"] = normalize_metric_type(kpi["type"])

            if "value" in kpi and isinstance(kpi["value"], dict) and "trend" in kpi["value"]:
                kpi["value"]["trend"] = normalize_trend_direction(kpi["value"]["trend"])

    return data


def normalize_sales_prospecting_report(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a SalesProspectingReport dictionary to ensure all enum values match expected values.

    Args:
        data: The input data dictionary representing a SalesProspectingReport

    Returns:
        A normalized dictionary with corrected enum values
    """
    if not data:
        return data

    # Normalize sales_metrics field
    if "sales_metrics" in data and isinstance(data["sales_metrics"], dict):
        data["sales_metrics"] = normalize_structured_data_report(data["sales_metrics"])

    return data
