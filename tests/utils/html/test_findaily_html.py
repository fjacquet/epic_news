"""Tests for Financial Daily HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.financial_report import FinancialReport
from epic_news.utils.html.fin_daily_html_factory import findaily_to_html
from epic_news.utils.html.template_renderers.financial_renderer import (
    FinancialRenderer,
)


@pytest.fixture
def sample_financial_report_data():
    """Provide a sample FinancialReport object for testing."""
    return FinancialReport(
        title="Test Financial Report",
        executive_summary="This is a test summary.",
        key_metrics={"P/E Ratio": "10"},
        analysis="This is a test analysis.",
        recommendations=["Buy"],
        analyses=[],
        suggestions=[],
    )


def test_findaily_to_html(sample_financial_report_data, tmp_path):
    """Test that findaily_to_html creates a valid HTML file."""
    html_file = tmp_path / "findaily_report.html"
    html_content = findaily_to_html(
        sample_financial_report_data, html_file=str(html_file)
    )

    assert html_file.exists()
    assert "Test Financial Report" in html_content
    assert "P/E Ratio" in html_content
    assert "Buy" in html_content


def test_financial_renderer(sample_financial_report_data):
    """Test the FinancialRenderer directly."""
    renderer = FinancialRenderer()
    html = renderer.render(sample_financial_report_data.model_dump())
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("h2").text == "💰 Rapport Financier"
    assert "This is a test summary." in soup.find("div", class_="executive-summary").text
    assert "P/E Ratio" in soup.find("div", class_="key-metrics").text
    assert "Buy" in soup.find("div", class_="recommendations").text
