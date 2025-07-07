"""Tests for Financial Daily HTML factory and renderer."""

import pytest

from epic_news.models.crews.financial_report import (
    AssetAnalysis,
    AssetSuggestion,
    FinancialReport,
)
from epic_news.utils.html.fin_daily_html_factory import findaily_to_html


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
    html_content = findaily_to_html(sample_financial_report_data, html_file=str(html_file))

    assert html_file.exists()
    assert "This is a test summary." in html_content
    assert "Stock analysis summary." in html_content
    assert "Buy Bitcoin" in html_content


@pytest.mark.skip(reason="Renderer is abstract class and can't be instantiated directly")
def test_financial_renderer(sample_financial_report_data):
    """Test the FinancialRenderer directly."""
    # Skipping this test as FinancialRenderer is an abstract class
    # that can't be instantiated directly
