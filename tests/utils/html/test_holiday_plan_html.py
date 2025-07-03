"""Tests for Holiday Plan HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup
from crewai import CrewOutput

from epic_news.models.holiday_plan import HolidayPlan
from epic_news.utils.html.holiday_plan_html_factory import holiday_plan_to_html
from epic_news.utils.html.template_renderers.holiday_plan_renderer import (
    HolidayPlanRenderer,
)


@pytest.fixture
def sample_holiday_plan_data():
    """Provide a sample HolidayPlan object for testing."""
    return HolidayPlan(
        introduction="Test holiday plan.",
        itineraire=[
            {
                "jour": "Jour 1",
                "activites": [{"heure": "10:00", "description": "Test activity"}],
            }
        ],
    )


def test_holiday_plan_to_html(sample_holiday_plan_data, tmp_path):
    """Test that holiday_plan_to_html creates a valid HTML file."""
    html_file = tmp_path / "holiday_plan_report.html"
    # Create a mock CrewOutput object
    crew_output = CrewOutput(
        raw=sample_holiday_plan_data.model_dump_json(),
        pydantic_output=sample_holiday_plan_data,
        tasks_output=[],
    )
    html_content = holiday_plan_to_html(crew_output, html_file=str(html_file))

    assert html_file.exists()
    assert "Test holiday plan." in html_content
    assert "Test activity" in html_content


def test_holiday_plan_renderer(sample_holiday_plan_data):
    """Test the HolidayPlanRenderer directly."""
    renderer = HolidayPlanRenderer()
    html = renderer.render(sample_holiday_plan_data.to_template_data())
    soup = BeautifulSoup(html, "html.parser")

    assert "Test holiday plan." in soup.find("section", class_="introduction-section").text
    assert "Test activity" in soup.find("section", class_="itinerary-section").text
