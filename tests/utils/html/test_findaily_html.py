"""Tests for Financial Daily HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.financial_report import (
    FinancialReport,
    AssetAnalysis,
    AssetSuggestion,
)
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
        analyses=[
            AssetAnalysis(
                asset_class="Stocks",
                summary="Stock analysis summary.",
                details=["Detail 1", "Detail 2"],
            )
        ],
        suggestions=[
            AssetSuggestion(
                asset_class="Crypto",
                suggestion="Buy Bitcoin",
                rationale="It's going to the moon!",
            )
        ],
        report_date="2025-01-01",
    )


def test_findaily_to_html(sample_financial_report_data, tmp_path):
    """Test that findaily_to_html creates a valid HTML file."""
    html_file = tmp_path / "findaily_report.html"
    html_content = findaily_to_html(
        sample_financial_report_data, html_file=str(html_file)
    )

    assert html_file.exists()
    assert "This is a test summary." in html_content
    assert "Stock analysis summary." in html_content
    assert "Buy Bitcoin" in html_content


def test_financial_renderer(sample_financial_report_data):
    """Test the FinancialRenderer directly."""
    renderer = FinancialRenderer()
    html = renderer.render(sample_financial_report_data.model_dump())
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("h2").text == "💰 Rapport Financier"
    assert "This is a test summary." in html
    assert "Stock analysis summary." in html
    assert "Buy Bitcoin" in html
