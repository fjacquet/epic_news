"""Tests for Meeting Prep HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.meeting_prep_report import MeetingPrepReport
from epic_news.utils.html.meeting_prep_html_factory import meeting_prep_to_html
from epic_news.utils.html.template_renderers.meeting_prep_renderer import (
    MeetingPrepRenderer,
)


@pytest.fixture
def sample_meeting_prep_data():
    """Provide a sample MeetingPrepReport object for testing."""
    return MeetingPrepReport(
        title="Test Meeting",
        summary="This is a test meeting.",
        company_profile={
            "name": "Test Company",
            "industry": "Testing",
            "market_position": "Leader in testing",
        },
        participants=[
            {
                "name": "Test Participant",
                "role": "Tester",
                "background": "A test participant",
            }
        ],
        industry_overview="The testing industry is growing.",
        talking_points=[],
        strategic_recommendations=[],
        additional_resources=[],
    )


def test_meeting_prep_to_html(sample_meeting_prep_data, tmp_path):
    """Test that meeting_prep_to_html creates a valid HTML file."""
    html_file = tmp_path / "meeting_prep_report.html"
    html_content = meeting_prep_to_html(
        sample_meeting_prep_data, html_file=str(html_file)
    )

    assert html_file.exists()
    assert "Test Meeting" in html_content
    assert "Test Company" in html_content
    assert "Test Participant" in html_content


def test_meeting_prep_renderer(sample_meeting_prep_data):
    """Test the MeetingPrepRenderer directly."""
    renderer = MeetingPrepRenderer()
    html = renderer.render(sample_meeting_prep_data.to_template_data())
    soup = BeautifulSoup(html, "html.parser")

    assert "Test Meeting" in soup.find("h2", class_="meeting-title").text
    assert "Test Company" in soup.find("div", class_="company-profile").text
    assert "Test Participant" in soup.find("div", class_="participants-list").text
