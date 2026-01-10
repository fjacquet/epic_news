"""Data-centric models for metrics, KPIs, and structured data reporting."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "MetricValue",
    "Metric",
    "KPI",
    "DataPoint",
    "DataSeries",
    "DataTable",
    "MetricType",
    "TrendDirection",
    "StructuredDataReport",
]


class MetricType(str, Enum):
    """Types of metrics that can be tracked."""

    NUMERIC = "numeric"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    RATING = "rating"
    BOOLEAN = "boolean"
    TEXT = "text"
    DATE = "date"
    DURATION = "duration"
    COUNT = "count"


class TrendDirection(str, Enum):
    """Possible trend directions for metrics."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class MetricValue(BaseModel):
    """A single metric value with optional comparison to previous period."""

    value: float | int | str | bool | datetime = Field(..., description="The current value of the metric")
    previous_value: float | int | str | bool | datetime | None = Field(
        None, description="The previous value of the metric for comparison"
    )
    change_percentage: float | None = Field(None, description="Percentage change from previous value")
    trend: TrendDirection = Field(default=TrendDirection.UNKNOWN, description="Direction of trend")

    @model_validator(mode="after")
    def calculate_change_and_trend(self) -> MetricValue:
        """Calculate change percentage and trend direction after validation."""
        # Calculate change percentage
        if self.change_percentage is None and self.previous_value is not None and self.value is not None:
            prev = self.previous_value
            curr = self.value

            if isinstance(prev, int | float) and isinstance(curr, int | float) and prev != 0:
                self.change_percentage = ((curr - prev) / abs(prev)) * 100

        # Determine trend
        if self.trend == TrendDirection.UNKNOWN and self.change_percentage is not None:
            change = self.change_percentage
            if change > 5:
                self.trend = TrendDirection.UP
            elif change < -5:
                self.trend = TrendDirection.DOWN
            else:
                self.trend = TrendDirection.STABLE
        return self


class Metric(BaseModel):
    """A named metric with value, type, and metadata."""

    name: str = Field(..., description="Name of the metric")
    display_name: str = Field(..., description="Display-friendly name of the metric")
    description: str = Field(..., description="Description of what the metric measures")
    value: MetricValue = Field(..., description="Current and historical values")
    type: MetricType = Field(..., description="Type of metric")
    unit: str | None = Field(None, description="Unit of measurement (e.g., '$', '%', 'days')")
    source: str | None = Field(None, description="Source of the metric data")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the metric was recorded")
    target: float | int | str | bool | None = Field(
        None, description="Target value for this metric if applicable"
    )
    is_key_metric: bool = Field(default=False, description="Whether this is a key metric to highlight")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about this metric"
    )


class KPI(Metric):
    """A Key Performance Indicator extending the base Metric with additional properties."""

    is_key_metric: bool = Field(default=True, description="KPIs are always key metrics")
    target: float | int | str | bool = Field(..., description="Target value for this KPI (required)")
    target_date: datetime | None = Field(None, description="Date by which the target should be reached")
    progress_percentage: float | None = Field(None, description="Percentage progress toward target")
    status: str = Field(
        default="pending", description="Status of this KPI (e.g., 'on track', 'at risk', 'achieved')"
    )

    @model_validator(mode="after")
    def calculate_progress_and_status(self) -> KPI:
        """Calculate progress percentage and status after validation."""
        # Calculate progress
        if self.progress_percentage is None and self.target is not None and self.value is not None:
            target = self.target
            curr_value = self.value.value

            if isinstance(target, int | float) and isinstance(curr_value, int | float) and target != 0:
                self.progress_percentage = (curr_value / target) * 100

        # Determine status
        if self.status == "pending" and self.progress_percentage is not None:
            progress = self.progress_percentage
            if progress >= 100:
                self.status = "achieved"
            elif progress >= 75:
                self.status = "on track"
            elif progress >= 50:
                self.status = "needs attention"
            else:
                self.status = "at risk"
        return self


class DataPoint(BaseModel):
    """A single data point with a label and value."""

    label: str = Field(..., description="Label for this data point")
    value: Any = Field(..., description="Value of this data point")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for this data point"
    )


class DataSeries(BaseModel):
    """A series of related data points."""

    name: str = Field(..., description="Name of this data series")
    description: str | None = Field(None, description="Description of this data series")
    points: list[DataPoint] = Field(..., description="Data points in this series")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata for this series")


class DataTable(BaseModel):
    """A structured table of data with columns and rows."""

    name: str = Field(..., description="Name of this data table")
    description: str | None = Field(None, description="Description of this data table")
    columns: list[str] = Field(..., description="Column headers")
    rows: list[list[Any]] = Field(..., description="Row data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata for this table")


class StructuredDataReport(BaseModel):
    """A comprehensive structured data report with metrics, KPIs, and data visualizations."""

    title: str = Field(..., description="Title of the report")
    description: str = Field(..., description="Description of what this report covers")
    metrics: list[Metric] = Field(default_factory=list, description="List of metrics included in this report")
    kpis: list[KPI] = Field(default_factory=list, description="List of KPIs included in this report")
    data_series: list[DataSeries] = Field(
        default_factory=list, description="List of data series included in this report"
    )
    data_tables: list[DataTable] = Field(
        default_factory=list, description="List of data tables included in this report"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="When this report was generated")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata for this report")
    html: str | None = Field(None, description="HTML representation of this report if available")
