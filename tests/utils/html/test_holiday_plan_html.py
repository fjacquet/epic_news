"""Tests for Holiday Planner HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup
from crewai import CrewOutput

from epic_news.models.crews.holiday_planner_report import HolidayPlannerReport
from epic_news.utils.html.holiday_planner_html_factory import holiday_planner_to_html
from epic_news.utils.html.template_renderers.holiday_renderer import HolidayRenderer


@pytest.fixture
def sample_holiday_planner_data():
    """Provide a sample HolidayPlannerReport object for testing."""
    return HolidayPlannerReport(
        introduction="Test holiday plan for Paris.",
        itinerary=[
            {
                "day": 1,
                "date": "2024-07-15",
                "activities": [
                    {
                        "time": "10:00-12:00",
                        "description": "Visit Eiffel Tower - Test activity at iconic landmark"
                    }
                ]
            }
        ],
        accommodations=[
            {
                "name": "Test Hotel",
                "address": "123 Test Street, Paris",
                "price_range": "€120/night",
                "description": "Comfortable test hotel with excellent amenities"
            }
        ],
        dining={
            "restaurants": [
                {
                    "name": "Test Restaurant",
                    "location": "456 Test Avenue, Paris",
                    "cuisine": "French",
                    "price_range": "€€€",
                    "description": "Excellent French cuisine with local specialties"
                }
            ]
        },
        budget={
            "items": [
                {
                    "category": "Accommodation",
                    "item": "Hotel booking",
                    "cost": "480",
                    "currency": "EUR",
                    "notes": "4 nights at Test Hotel"
                }
            ],
            "total_estimated": "800",
            "currency": "EUR"
        }
    )


def test_holiday_planner_to_html(sample_holiday_planner_data, tmp_path):
    """Test that holiday_planner_to_html creates a valid HTML file."""
    html_file = tmp_path / "holiday_planner_report.html"
    # Create a mock CrewOutput object
    crew_output = CrewOutput(
        raw=sample_holiday_planner_data.model_dump_json(),
        pydantic_output=sample_holiday_planner_data,
        tasks_output=[],
    )
    html_content = holiday_planner_to_html(crew_output, html_file=str(html_file))

    assert html_file.exists()
    assert "Test holiday plan for Paris" in html_content
    assert "Visit Eiffel Tower" in html_content
    assert "Test Hotel" in html_content


def test_holiday_renderer(sample_holiday_planner_data):
    """Test the HolidayRenderer directly."""
    renderer = HolidayRenderer()
    html = renderer.render(sample_holiday_planner_data.to_template_data())
    soup = BeautifulSoup(html, "html.parser")

    # Test that key sections are present
    assert "Test holiday plan for Paris" in html
    assert "Visit Eiffel Tower" in html
    assert "Test Hotel" in html
    assert "Test Restaurant" in html

    # Test HTML structure
    assert soup.find("section", class_="introduction") is not None
    assert soup.find("section", class_="itinerary") is not None
    assert soup.find("section", class_="accommodations") is not None
    assert soup.find("section", class_="dining") is not None
    assert soup.find("section", class_="budget") is not None
