"""Tests for Poem HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.poem_models import PoemJSONOutput
from epic_news.utils.html.poem_html_factory import poem_to_html
from epic_news.utils.html.template_renderers.poem_renderer import PoemRenderer


@pytest.fixture
def sample_poem_data():
    """Provide a sample PoemJSONOutput object for testing."""
    return PoemJSONOutput(
        title="Ode to Tests",
        poem="Line 1\nLine 2",
    )


def test_poem_to_html(sample_poem_data, tmp_path):
    """Test that poem_to_html creates a valid HTML file."""
    html_file = tmp_path / "poem_report.html"
    html_content = poem_to_html(sample_poem_data, html_file=str(html_file))

    assert html_file.exists()
    assert "Ode to Tests" in html_content
    assert "Line 1" in html_content
    assert "This is a test poem." in html_content


def test_poem_renderer(sample_poem_data):
    """Test the PoemRenderer directly."""
    renderer = PoemRenderer()
    html = renderer.render(sample_poem_data.model_dump())
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("h2").text == "🌌 Ode to Tests"
    assert "Line 1" in soup.find("div", class_="full-poem").text
    assert "This is a test poem." in soup.find("div", class_="poem-analysis").text
