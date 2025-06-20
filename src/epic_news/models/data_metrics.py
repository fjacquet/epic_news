"""Data-centric models for metrics, KPIs, and structured data reporting."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "MetricValue", 
    "Metric", 
    "KPI", 
    "DataPoint", 
    "DataSeries", 
    "DataTable", 
    "MetricType",
    "TrendDirection",
    "StructuredDataReport"
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
    
    value: Union[float, int, str, bool, datetime] = Field(
        ..., description="The current value of the metric"
    )
    previous_value: Optional[Union[float, int, str, bool, datetime]] = Field(
        None, description="The previous value of the metric for comparison"
    )
    change_percentage: Optional[float] = Field(
        None, description="Percentage change from previous value"
    )
    trend: TrendDirection = Field(
        default=TrendDirection.UNKNOWN, description="Direction of trend"
    )
    
    @field_validator("change_percentage")
    def validate_change_percentage(cls, v, values):
        """Calculate change percentage if not provided but previous value exists."""
        if v is None and "previous_value" in values.data and "value" in values.data:
            prev = values.data["previous_value"]
            curr = values.data["value"]
            
            # Only calculate for numeric types
            if (isinstance(prev, (int, float)) and 
                isinstance(curr, (int, float)) and 
                prev != 0):
                return ((curr - prev) / abs(prev)) * 100
        return v
    
    @field_validator("trend")
    def validate_trend(cls, v, values):
        """Determine trend direction if not explicitly provided."""
        if v == TrendDirection.UNKNOWN and "change_percentage" in values.data:
            change = values.data["change_percentage"]
            if change is not None:
                if change > 5:
                    return TrendDirection.UP
                elif change < -5:
                    return TrendDirection.DOWN
                else:
                    return TrendDirection.STABLE
        return v


class Metric(BaseModel):
    """A named metric with value, type, and metadata."""
    
    name: str = Field(..., description="Name of the metric")
    display_name: str = Field(..., description="Display-friendly name of the metric")
    description: str = Field(..., description="Description of what the metric measures")
    value: MetricValue = Field(..., description="Current and historical values")
    type: MetricType = Field(..., description="Type of metric")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., '$', '%', 'days')")
    source: Optional[str] = Field(None, description="Source of the metric data")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the metric was recorded")
    target: Optional[Union[float, int, str, bool]] = Field(
        None, description="Target value for this metric if applicable"
    )
    is_key_metric: bool = Field(
        default=False, description="Whether this is a key metric to highlight"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about this metric"
    )


class KPI(Metric):
    """A Key Performance Indicator extending the base Metric with additional properties."""
    
    is_key_metric: bool = Field(
        default=True, description="KPIs are always key metrics"
    )
    target: Union[float, int, str, bool] = Field(
        ..., description="Target value for this KPI (required)"
    )
    target_date: Optional[datetime] = Field(
        None, description="Date by which the target should be reached"
    )
    progress_percentage: Optional[float] = Field(
        None, description="Percentage progress toward target"
    )
    status: str = Field(
        default="pending", description="Status of this KPI (e.g., 'on track', 'at risk', 'achieved')"
    )
    
    @field_validator("progress_percentage")
    def calculate_progress(cls, v, values):
        """Calculate progress percentage if not provided but target exists."""
        if v is None and "target" in values.data and "value" in values.data:
            target = values.data["target"]
            curr_value = values.data["value"].value
            
            # Only calculate for numeric types
            if (isinstance(target, (int, float)) and 
                isinstance(curr_value, (int, float)) and
                target != 0):
                return (curr_value / target) * 100
        return v
    
    @field_validator("status")
    def determine_status(cls, v, values):
        """Determine KPI status based on progress if not explicitly provided."""
        if v == "pending" and "progress_percentage" in values.data:
            progress = values.data["progress_percentage"]
            if progress is not None:
                if progress >= 100:
                    return "achieved"
                elif progress >= 75:
                    return "on track"
                elif progress >= 50:
                    return "needs attention"
                else:
                    return "at risk"
        return v


class DataPoint(BaseModel):
    """A single data point with a label and value."""
    
    label: str = Field(..., description="Label for this data point")
    value: Any = Field(..., description="Value of this data point")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for this data point"
    )


class DataSeries(BaseModel):
    """A series of related data points."""
    
    name: str = Field(..., description="Name of this data series")
    description: Optional[str] = Field(None, description="Description of this data series")
    points: List[DataPoint] = Field(..., description="Data points in this series")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for this series"
    )


class DataTable(BaseModel):
    """A structured table of data with columns and rows."""
    
    name: str = Field(..., description="Name of this data table")
    description: Optional[str] = Field(None, description="Description of this data table")
    columns: List[str] = Field(..., description="Column headers")
    rows: List[List[Any]] = Field(..., description="Row data")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for this table"
    )


class StructuredDataReport(BaseModel):
    """A comprehensive structured data report with metrics, KPIs, and data visualizations."""
    
    title: str = Field(..., description="Title of the report")
    description: str = Field(..., description="Description of what this report covers")
    metrics: List[Metric] = Field(
        default_factory=list, description="List of metrics included in this report"
    )
    kpis: List[KPI] = Field(
        default_factory=list, description="List of KPIs included in this report"
    )
    data_series: List[DataSeries] = Field(
        default_factory=list, description="List of data series included in this report"
    )
    data_tables: List[DataTable] = Field(
        default_factory=list, description="List of data tables included in this report"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this report was generated"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for this report"
    )
    html: Optional[str] = Field(
        None, description="HTML representation of this report if available"
    )
