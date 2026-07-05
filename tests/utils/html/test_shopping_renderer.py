"""Tests for the ShoppingRenderer (crew_identifier: SHOPPING).

The renderer consumes ``ShoppingAdviceOutput.model_dump()`` directly, exactly
as produced in ``main.generate_shopping_advice`` ->
``render_and_write_html("SHOPPING", model)``. These tests pin the real model
contract. The pre-fix renderer read flat keys (``product_name``,
``price_comparison``, ``recommendation``, ``alternatives``, top-level
``pros``/``cons``) that ``model_dump()`` never produces, so every section was
silently dropped and the report rendered as an empty wrapper.
"""

from epic_news.models.crews.shopping_advice_report import (
    CompetitorInfo,
    PriceInfo,
    ProductInfo,
    ShoppingAdviceOutput,
)
from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.shopping_renderer import ShoppingRenderer

CREW_IDENTIFIER = "SHOPPING"


def _full_model() -> ShoppingAdviceOutput:
    return ShoppingAdviceOutput(
        product_info=ProductInfo(
            name="Aspirateur X",
            overview="Un aspirateur puissant et léger.",
            key_specifications=["500 W", "Sans sac"],
            pros=["Léger", "Silencieux"],
            cons=["Autonomie limitée"],
            target_audience="Petits appartements",
            common_issues=["Filtre à nettoyer souvent"],
        ),
        switzerland_prices=[
            PriceInfo(
                retailer="Digitec",
                price="299 CHF",
                url="https://digitec.ch/x",
                shipping_cost="0 CHF",
                total_cost="299 CHF",
                notes="En stock",
            )
        ],
        france_prices=[
            PriceInfo(
                retailer="Fnac",
                price="279 €",
                url=None,
                shipping_cost="9 €",
                total_cost="288 €",
                notes="Sous 3 jours",
            )
        ],
        competitors=[
            CompetitorInfo(
                name="Aspirateur Y",
                price_range="200-250 €",
                key_features=["Moins cher", "Plus lourd"],
                pros=["Prix"],
                cons=["Bruyant"],
                target_audience="Budget serré",
            )
        ],
        executive_summary="Le X est recommandé pour son rapport qualité/prix.",
        final_recommendations="Acheter le X chez Digitec.",
        best_deals=["Digitec — 299 CHF port gratuit"],
        user_preferences_context="Budget 300 CHF, logement 2 pièces.",
    )


def test_full_model_via_template_manager_renders_all_sections():
    html = TemplateManager().render_report(CREW_IDENTIFIER, _full_model().model_dump())

    # Product overview (from product_info -- the pre-fix bug rendered NONE of this)
    assert "🛍️ Aspirateur X" in html
    assert "Un aspirateur puissant et léger." in html
    assert "Petits appartements" in html
    assert "<li>500 W</li>" in html  # key_specifications
    assert "Filtre à nettoyer souvent" in html  # common_issues

    # Executive summary
    assert "Le X est recommandé pour son rapport qualité/prix." in html

    # Prices: both countries; retailer linked when a url is present
    assert "🇨🇭 Suisse" in html
    assert "🇫🇷 France" in html
    assert '<a href="https://digitec.ch/x"' in html
    assert "299 CHF" in html
    assert "288 €" in html

    # Pros/cons (from product_info)
    assert "Léger" in html
    assert "Autonomie limitée" in html

    # Competitors as alternatives
    assert "Aspirateur Y (200-250 €)" in html
    assert "Budget serré" in html

    # Best deals + final recommendation + user context
    assert "Digitec — 299 CHF port gratuit" in html
    assert "Acheter le X chez Digitec." in html
    assert "Budget 300 CHF, logement 2 pièces." in html

    # Report <title> derives from product_info.name, not the generic fallback.
    assert "🛒 Aspirateur X - Conseil d'Achat" in html


def test_regression_model_dump_is_not_blank():
    """The exact production shape must produce real content, not an empty wrapper."""
    html = ShoppingRenderer().render(_full_model().model_dump())
    # Pre-fix this was essentially just <div class="shopping-advice"></div>.
    assert html.count("<section") >= 5
    assert "Aspirateur X" in html


def test_error_key_renders_error_only():
    html = ShoppingRenderer().render({"error": "No shopping advice data available"})
    assert "⚠️ No shopping advice data available" in html
    assert "<section" not in html


def test_empty_dict_renders_empty_state_not_blank():
    html = ShoppingRenderer().render({})
    assert '<div class="shopping-advice">' in html
    assert "<section" not in html
    # A degenerate payload is signalled visibly, not returned silently blank.
    assert 'class="empty-state"' in html


def test_unsafe_url_scheme_is_not_hyperlinked():
    """A javascript:/data: retailer URL must render as plain text, never an href."""
    model = _full_model().model_dump()
    model["switzerland_prices"][0]["url"] = "javascript:alert(1)"
    model["france_prices"][0]["url"] = "data:text/html,<script>x</script>"
    html = ShoppingRenderer().render(model)
    assert "javascript:" not in html
    assert "data:text/html" not in html
    assert "<a " not in html  # neither retailer is hyperlinked now
    # Retailers still shown as plain text.
    assert "Digitec" in html
    assert "Fnac" in html


def test_price_row_without_url_is_plain_text():
    html = ShoppingRenderer().render(_full_model().model_dump())
    # Swiss retailer (has url) is linked; French retailer (url=None) is plain text.
    assert '<a href="https://digitec.ch/x"' in html
    assert "Fnac" in html
    assert ">Fnac</a>" not in html


def test_nested_tags_use_correct_class_attribute():
    html = ShoppingRenderer().render(_full_model().model_dump())
    assert 'class="product-overview"' in html
    assert 'class="price-table"' in html
    # The old broken literal-underscore attribute must never appear.
    assert 'class_="product-overview"' not in html


def test_malformed_input_degrades_gracefully_without_crash():
    """Defensive: a non-dict product_info and non-dict list items are skipped, no crash."""
    html = ShoppingRenderer().render(
        {
            "product_info": "not-a-dict",  # overview + pros/cons guards skip
            "switzerland_prices": ["not-a-dict", {"retailer": "R", "price": "1"}],
            "france_prices": [],
            "competitors": ["not-a-dict", {"name": "C", "price_range": "x"}],
            "executive_summary": "S",
        }
    )
    # product_info isn't a dict -> the overview/pros-cons sections are skipped.
    assert "🛍️" not in html
    assert "Avantages et" not in html
    # Valid list items still render; the non-dict entries are skipped, no crash.
    assert "<td>R</td>" in html
    assert "C (x)" in html

    # product_info present but missing name/overview -> overview section skipped.
    html2 = ShoppingRenderer().render({"product_info": {"target_audience": "X"}})
    assert "product-overview" not in html2


def test_missing_optional_sections_are_skipped():
    """A model-valid product with empty lists skips optional sections cleanly."""
    model = ShoppingAdviceOutput(
        product_info=ProductInfo(
            name="Simple",
            overview="Basique.",
            key_specifications=[],
            pros=[],
            cons=[],
            target_audience="Tous",
            common_issues=[],
        ),
        switzerland_prices=[],
        france_prices=[],
        competitors=[],
        executive_summary="Résumé.",
        final_recommendations="Recommandation.",
        best_deals=[],
        user_preferences_context="Contexte.",
    )
    html = ShoppingRenderer().render(model.model_dump())
    assert "🛍️ Simple" in html
    assert "💰 Comparaison des Prix" not in html  # no prices
    assert "🔄 Alternatives" not in html  # no competitors
    assert "Avantages et" not in html  # no pros/cons
    assert "🏆 Meilleures Offres" not in html  # no best_deals
    assert "🌟 Recommandation Finale" in html  # present
