import re

import pytest

from epic_news.models.crews.financial_report import (
    AssetAnalysis,
    AssetSuggestion,
    FinancialReport,
)
from epic_news.models.crews.shopping_advice_report import (
    CompetitorInfo,
    PriceInfo,
    ProductInfo,
    ShoppingAdviceOutput,
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
    # Mirrors production input to render_report: main.generate_shopping_advice ->
    # render_and_write_html("SHOPPING", model) passes model.model_dump().
    return ShoppingAdviceOutput(
        product_info=ProductInfo(
            name="Robot de cuisine",
            overview="Un robot polyvalent pour la cuisine quotidienne.",
            key_specifications=["1000 W", "Bol 5 L", "10 vitesses"],
            pros=["Silencieux", "Facile à nettoyer"],
            cons=["Accessoires limités"],
            target_audience="Familles cuisinant au quotidien",
            common_issues=["Joint du bol à remplacer après 2 ans"],
        ),
        switzerland_prices=[
            PriceInfo(
                retailer="Boutique A",
                price="199 CHF",
                url="https://example.ch/a",
                shipping_cost="0 CHF",
                total_cost="199 CHF",
                notes="En stock",
            )
        ],
        france_prices=[
            PriceInfo(
                retailer="Boutique B",
                price="189 €",
                url=None,
                shipping_cost="5 €",
                total_cost="194 €",
                notes="Livraison 48h",
            )
        ],
        competitors=[
            CompetitorInfo(
                name="Modèle B",
                price_range="150-180 €",
                key_features=["Compact", "Moins cher"],
                pros=["Prix attractif"],
                cons=["Moins puissant"],
                target_audience="Petits budgets",
            )
        ],
        executive_summary="Le Robot de cuisine offre le meilleur rapport qualité/prix.",
        final_recommendations="Acheter en Suisse chez Boutique A.",
        best_deals=["Boutique A — 199 CHF port gratuit"],
        user_preferences_context="Budget max 250 CHF, usage familial.",
    ).model_dump()


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
