"""Data-centric tools for metrics, KPIs, and structured data reporting."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Union

from crewai.tools import BaseTool
from jinja2 import Environment, FileSystemLoader
from langchain.tools import BaseTool as LangchainBaseTool

from epic_news.models.data_metrics import (
    KPI,
    DataPoint,
    DataSeries,
    DataTable,
    Metric,
    MetricType,
    StructuredDataReport,
    TrendDirection,
)

__all__ = [
    "MetricsCalculatorTool",
    "KPITrackerTool",
    "DataVisualizationTool",
    "StructuredReportTool",
    "get_data_centric_tools",
]


class MetricsCalculatorTool(BaseTool):
    """Tool for calculating and tracking metrics from data."""

    name: str = "MetricsCalculatorTool"
    description: str = """
    Calculate and track metrics from structured data. This tool helps you:
    1. Create new metrics with proper typing and validation
    2. Calculate changes and trends over time
    3. Format metrics for display with appropriate units
    
    Input should be a JSON object with:
    - name: Name of the metric
    - display_name: Display-friendly name
    - description: Description of what the metric measures
    - value: Current value of the metric
    - previous_value: (Optional) Previous value for comparison
    - type: Type of metric (numeric, percentage, currency, rating, boolean, text, date, duration, count)
    - unit: (Optional) Unit of measurement
    - source: (Optional) Source of the data
    - target: (Optional) Target value if applicable
    - is_key_metric: (Optional) Whether this is a key metric
    
    Output will be a properly formatted Metric object with calculated trends and changes.
    """

    def _run(self, name: str, display_name: str, description: str,
             value: Any, type: str, previous_value: Any | None = None,
             unit: str | None = None, source: str | None = None,
             target: Any | None = None, is_key_metric: bool = False,
             **kwargs) -> dict[str, Any]:
        """Run the metrics calculator tool."""
        try:
            # Validate metric type
            metric_type = MetricType(type.lower())

            # Create metric value with trend calculation
            metric_value = {
                "value": value,
                "previous_value": previous_value,
                # Let the model validators handle calculations
            }

            # Create the metric
            metric = Metric(
                name=name,
                display_name=display_name,
                description=description,
                value=metric_value,
                type=metric_type,
                unit=unit,
                source=source,
                target=target,
                is_key_metric=is_key_metric,
                timestamp=datetime.now(),
                metadata=kwargs.get("metadata", {})
            )

            # Return as dictionary for easier consumption by LLMs
            return metric.model_dump()

        except Exception as e:
            return {"error": f"Failed to calculate metric: {str(e)}"}


class KPITrackerTool(BaseTool):
    """Tool for tracking Key Performance Indicators (KPIs)."""

    name: str = "KPITrackerTool"
    description: str = """
    Track and manage Key Performance Indicators (KPIs). This tool helps you:
    1. Create new KPIs with targets and deadlines
    2. Calculate progress toward targets
    3. Determine KPI status (on track, at risk, achieved)
    
    Input should be a JSON object with:
    - name: Name of the KPI
    - display_name: Display-friendly name
    - description: Description of what the KPI measures
    - value: Current value of the KPI
    - previous_value: (Optional) Previous value for comparison
    - type: Type of KPI (numeric, percentage, currency, rating, boolean, text, date, duration, count)
    - unit: (Optional) Unit of measurement
    - source: (Optional) Source of the data
    - target: Target value (required for KPIs)
    - target_date: (Optional) Date by which target should be reached
    
    Output will be a properly formatted KPI object with calculated progress and status.
    """

    def _run(self, name: str, display_name: str, description: str,
             value: Any, type: str, target: Any,
             previous_value: Any | None = None, unit: str | None = None,
             source: str | None = None, target_date: str | None = None,
             **kwargs) -> dict[str, Any]:
        """Run the KPI tracker tool."""
        try:
            # Validate metric type
            metric_type = MetricType(type.lower())

            # Parse target date if provided
            parsed_target_date = None
            if target_date:
                try:
                    parsed_target_date = datetime.fromisoformat(target_date)
                except ValueError:
                    parsed_target_date = None

            # Create metric value with trend calculation
            metric_value = {
                "value": value,
                "previous_value": previous_value,
                # Let the model validators handle calculations
            }

            # Create the KPI
            kpi = KPI(
                name=name,
                display_name=display_name,
                description=description,
                value=metric_value,
                type=metric_type,
                unit=unit,
                source=source,
                target=target,
                target_date=parsed_target_date,
                timestamp=datetime.now(),
                metadata=kwargs.get("metadata", {})
                # Let the model validators handle progress and status
            )

            # Return as dictionary for easier consumption by LLMs
            return kpi.model_dump()

        except Exception as e:
            return {"error": f"Failed to track KPI: {str(e)}"}


class DataVisualizationTool(BaseTool):
    """Tool for creating data visualizations from structured data."""

    name: str = "DataVisualizationTool"
    description: str = """
    Create data visualizations from structured data. This tool helps you:
    1. Format data for visualization
    2. Generate visualization configurations
    3. Create data series and tables for reporting
    
    Input should be a JSON object with either:
    - For data series:
      - type: "series"
      - name: Name of the data series
      - description: (Optional) Description of the series
      - points: List of data points with label and value
    
    - For data tables:
      - type: "table"
      - name: Name of the data table
      - description: (Optional) Description of the table
      - columns: List of column headers
      - rows: List of rows (each row is a list of values)
    
    Output will be a properly formatted data structure ready for visualization.
    """

    def _run(self, type: str, name: str, **kwargs) -> dict[str, Any]:
        """Run the data visualization tool."""
        try:
            if type.lower() == "series":
                # Create a data series
                points = []
                for point in kwargs.get("points", []):
                    points.append(DataPoint(
                        label=point.get("label", ""),
                        value=point.get("value"),
                        metadata=point.get("metadata", {})
                    ))

                series = DataSeries(
                    name=name,
                    description=kwargs.get("description"),
                    points=points,
                    metadata=kwargs.get("metadata", {})
                )

                return series.model_dump()

            if type.lower() == "table":
                # Create a data table
                table = DataTable(
                    name=name,
                    description=kwargs.get("description"),
                    columns=kwargs.get("columns", []),
                    rows=kwargs.get("rows", []),
                    metadata=kwargs.get("metadata", {})
                )

                return table.model_dump()

            return {"error": f"Unknown visualization type: {type}"}

        except Exception as e:
            return {"error": f"Failed to create data visualization: {str(e)}"}


class StructuredReportTool(BaseTool):
    """Tool for generating structured data reports with metrics, KPIs, and visualizations."""

    name: str = "StructuredReportTool"
    description: str = """
    Generate comprehensive structured data reports. This tool helps you:
    1. Combine metrics, KPIs, and data visualizations into a single report
    2. Format the report for presentation
    3. Generate HTML output for the report
    
    Input should be a JSON object with:
    - title: Title of the report
    - description: Description of what the report covers
    - metrics: (Optional) List of metrics to include
    - kpis: (Optional) List of KPIs to include
    - data_series: (Optional) List of data series to include
    - data_tables: (Optional) List of data tables to include
    
    Output will be a structured data report with all components properly formatted.
    """

    def _run(self, title: str, description: str, **kwargs) -> dict[str, Any]:
        """Run the structured report tool."""
        try:
            # Process metrics if provided
            metrics = []
            for metric_data in kwargs.get("metrics", []):
                # Create metric value
                metric_value = {
                    "value": metric_data.get("value"),
                    "previous_value": metric_data.get("previous_value"),
                    "change_percentage": metric_data.get("change_percentage"),
                    "trend": metric_data.get("trend", TrendDirection.UNKNOWN)
                }

                # Create metric
                metrics.append(Metric(
                    name=metric_data.get("name", ""),
                    display_name=metric_data.get("display_name", ""),
                    description=metric_data.get("description", ""),
                    value=metric_value,
                    type=metric_data.get("type", MetricType.NUMERIC),
                    unit=metric_data.get("unit"),
                    source=metric_data.get("source"),
                    target=metric_data.get("target"),
                    is_key_metric=metric_data.get("is_key_metric", False),
                    timestamp=datetime.now(),
                    metadata=metric_data.get("metadata", {})
                ))

            # Process KPIs if provided
            kpis = []
            for kpi_data in kwargs.get("kpis", []):
                # Create metric value
                metric_value = {
                    "value": kpi_data.get("value"),
                    "previous_value": kpi_data.get("previous_value"),
                    "change_percentage": kpi_data.get("change_percentage"),
                    "trend": kpi_data.get("trend", TrendDirection.UNKNOWN)
                }

                # Create KPI
                kpis.append(KPI(
                    name=kpi_data.get("name", ""),
                    display_name=kpi_data.get("display_name", ""),
                    description=kpi_data.get("description", ""),
                    value=metric_value,
                    type=kpi_data.get("type", MetricType.NUMERIC),
                    unit=kpi_data.get("unit"),
                    source=kpi_data.get("source"),
                    target=kpi_data.get("target", 0),
                    target_date=kpi_data.get("target_date"),
                    progress_percentage=kpi_data.get("progress_percentage"),
                    status=kpi_data.get("status", "pending"),
                    timestamp=datetime.now(),
                    metadata=kpi_data.get("metadata", {})
                ))

            # Process data series if provided
            data_series = []
            for series_data in kwargs.get("data_series", []):
                points = []
                for point in series_data.get("points", []):
                    points.append(DataPoint(
                        label=point.get("label", ""),
                        value=point.get("value"),
                        metadata=point.get("metadata", {})
                    ))

                data_series.append(DataSeries(
                    name=series_data.get("name", ""),
                    description=series_data.get("description"),
                    points=points,
                    metadata=series_data.get("metadata", {})
                ))

            # Process data tables if provided
            data_tables = []
            for table_data in kwargs.get("data_tables", []):
                data_tables.append(DataTable(
                    name=table_data.get("name", ""),
                    description=table_data.get("description"),
                    columns=table_data.get("columns", []),
                    rows=table_data.get("rows", []),
                    metadata=table_data.get("metadata", {})
                ))

            # Create the structured report
            report = StructuredDataReport(
                title=title,
                description=description,
                metrics=metrics,
                kpis=kpis,
                data_series=data_series,
                data_tables=data_tables,
                timestamp=datetime.now(),
                metadata=kwargs.get("metadata", {})
            )

            # Generate HTML if requested
            if kwargs.get("generate_html", False):
                # Get the path to the templates directory
                templates_dir = os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..", "..", "..", "templates"
                    )
                )

                # Create Jinja2 environment
                env = Environment(loader=FileSystemLoader(templates_dir))
                template = env.get_template("data_report_template.html")

                # Render the template
                html = template.render(
                    title=report.title,
                    description=report.description,
                    metrics=report.metrics,
                    kpis=report.kpis,
                    data_series=report.data_series,
                    data_tables=report.data_tables,
                    timestamp=report.timestamp,
                    metadata=report.metadata
                )

                # Add the HTML to the report
                report.html = html

            # Return as dictionary for easier consumption by LLMs
            return report.model_dump()

        except Exception as e:
            return {"error": f"Failed to generate structured report: {str(e)}"}


def get_data_centric_tools() -> list[Union[BaseTool, LangchainBaseTool]]:
    """Get a list of all data-centric tools."""
    return [
        MetricsCalculatorTool(),
        KPITrackerTool(),
        DataVisualizationTool(),
        StructuredReportTool(),
    ]
