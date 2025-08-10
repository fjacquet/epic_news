import re

import pytest

from epic_news.models.crews.financial_report import (
    AssetAnalysis,
    AssetSuggestion,
    FinancialReport,
)
from epic_news.utils.html.template_manager import TemplateManager


def sanitize_dynamic(html: str) -> str:
    """Normalize dynamic parts to make snapshots stable."""
    # Normalize generation date in the universal template header
    html = re.sub(
        r"Généré le [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}",
        "Généré le 2025-01-01 00:00:00",
        html,
    )
    return html


def assert_basic_html(html: str) -> None:
    """Quick sanity checks on produced HTML."""
    assert "<!DOCTYPE html>" in html
    assert "<html" in html and "<head" in html and "<body" in html
    # No leftover Jinja or templating tokens
    assert "{{" not in html and "{%" not in html


def build_findaily():
    return FinancialReport(
        title="Daily Financial Report",
        executive_summary="Les marchés montent légèrement.",
        analyses=[
            AssetAnalysis(
                asset_class="Stocks",
                summary="Les actions progressent",
                details=["S&P 500 +1.0%", "NASDAQ +1.5%"],
            )
        ],
        suggestions=[
            AssetSuggestion(
                asset_class="Stocks",
                suggestion="Acheter QQQ",
                rationale="Momentum fort",
            )
        ],
        report_date="2025-08-10",
    )


def build_newsdaily():
    return {
        "summary": "Points clés du jour.",
        "france": [
            {
                "titre": "Réforme adoptée",
                "date": "2025-08-10",
                "source": "Le Monde",
                "url": "https://example.com/article",
                "resume": "Description brève de l'article",
            }
        ],
    }


def build_shopping():
    return {
        "product_name": "Robot de cuisine",
        "product_overview": "Un robot polyvalent pour la cuisine quotidienne.",
        "price_comparison": [{"vendor": "Boutique A", "price": "199€", "availability": "En stock"}],
        "recommendation": "Acheter",
        "recommendation_rationale": "Bon rapport qualité/prix",
        "alternatives": [{"name": "Modèle B", "reason": "Moins cher"}],
        "pros": ["Silencieux", "Facile à nettoyer"],
        "cons": ["Accessoires limités"],
    }


@pytest.mark.parametrize(
    "selected_crew,data_builder",
    [
        ("FINDAILY", build_findaily),
        ("NEWSDAILY", build_newsdaily),
        ("SHOPPING", build_shopping),
    ],
)
def test_template_manager_rendering_snapshots(selected_crew, data_builder, file_regression):
    tm = TemplateManager()
    data = data_builder()
    html = tm.render_report(selected_crew, data)
    html = sanitize_dynamic(html)

    assert_basic_html(html)

    # Store HTML snapshots next to this test (pytest-regressions)
    file_regression.check(html, extension=".html", encoding="utf-8")
