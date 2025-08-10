import json

from epic_news.tools._json_utils import ensure_json_str
from epic_news.tools.data_centric_tools import (
    DataVisualizationTool,
    KPITrackerTool,
    StructuredReportTool,
)


def test_ensure_json_str_from_dict():
    s = ensure_json_str({"a": 1})
    assert isinstance(s, str)
    obj = json.loads(s)
    assert obj == {"a": 1}


def test_ensure_json_str_from_text():
    s = ensure_json_str("hello")
    assert isinstance(s, str)
    obj = json.loads(s)
    assert obj == {"result": "hello"}


def test_data_visualization_series_returns_json():
    tool = DataVisualizationTool()
    s = tool._run(
        type="series",
        name="Revenue",
        points=[
            {"label": "Q1", "value": 100},
            {"label": "Q2", "value": 120},
        ],
    )
    assert isinstance(s, str)
    data = json.loads(s)
    assert data["name"] == "Revenue"
    assert len(data["points"]) == 2


def test_kpi_tracker_returns_json():
    tool = KPITrackerTool()
    s = tool._run(
        name="conversion_rate",
        display_name="Conversion Rate",
        description="Website conversion rate",
        value=5.0,
        type="numeric",
        target=6.0,
        previous_value=4.0,
        unit="%",
    )
    assert isinstance(s, str)
    data = json.loads(s)
    assert data["name"] == "conversion_rate"
    assert data["display_name"] == "Conversion Rate"


def test_structured_report_returns_json():
    tool = StructuredReportTool()
    s = tool._run(title="Weekly Report", description="Summary")
    assert isinstance(s, str)
    data = json.loads(s)
    assert data["title"] == "Weekly Report"
