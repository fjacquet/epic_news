"""Tests for the FinancialRenderer (crew_identifier: FINDAILY).

The renderer consumes exactly the ``FinancialReport`` model contract:
``title``, ``executive_summary``, ``analyses`` (list of ``AssetAnalysis``),
``suggestions`` (list of ``AssetSuggestion``), ``report_date``. Data always
reaches it as ``FinancialReport.model_dump()`` through ``TemplateManager``
(the legacy fallback path runs ``FinancialReport.model_validate`` first,
which drops unknown keys), so the previously-present free-form legacy keys
(``summary``, ``analysis``, ``detailed_analysis``, ``recommendations``,
``advice``, ``date``, ``key_metrics``/``metrics``) were unreachable dead code
and have been removed.

Nested tags are built with ``soup.new_tag(tag, attrs={"class": "..."})``,
producing a correct ``class="..."`` attribute; tests assert that form.
"""

from epic_news.models.crews.financial_report import (
    AssetAnalysis,
    AssetSuggestion,
    FinancialReport,
)
from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.financial_renderer import FinancialRenderer

CREW_IDENTIFIER = "FINDAILY"


# ---------------------------------------------------------------------------
# Full pipeline tests via TemplateManager (real FinancialReport model)
# ---------------------------------------------------------------------------


def test_full_report_via_template_manager():
    """Full FinancialReport with multiple analyses/suggestions renders expected content."""
    report = FinancialReport(
        title="Custom Title",
        executive_summary="Les marchés ont connu une semaine volatile.",
        analyses=[
            AssetAnalysis(
                asset_class="Actions",
                summary="Les actions technologiques ont surperformé.",
                details=["NVDA +5%", "AAPL -1%"],
            ),
            AssetAnalysis(
                asset_class="Obligations",
                summary="Les taux se sont stabilisés.",
                details=[],  # empty details -> no <ul> for this section
            ),
        ],
        suggestions=[
            AssetSuggestion(
                asset_class="Crypto",
                suggestion="Acheter du Bitcoin",
                rationale="Momentum haussier confirmé.",
            ),
        ],
        report_date="2026-07-04",
    )

    html = TemplateManager().render_report(CREW_IDENTIFIER, report.model_dump())

    # Header uses the report's `title` field
    assert "💰 Custom Title" in html
    assert "📅 2026-07-04" in html

    # Executive summary
    assert "Les marchés ont connu une semaine volatile." in html

    # Analyses (asset_class heading, summary, details list)
    assert "Actions" in html
    assert "Les actions technologiques ont surperformé." in html
    assert "NVDA +5%" in html
    assert "AAPL -1%" in html
    assert "Obligations" in html
    assert "Les taux se sont stabilisés." in html

    # Suggestions combine asset_class/suggestion/rationale
    assert "[Crypto] Acheter du Bitcoin" in html
    assert "→ Momentum haussier confirmé." in html

    # The fallback header text must NOT appear since a custom title was given.
    assert "Rapport Financier" not in html

    # Only the "Actions" section's non-empty details produced a <ul>.
    assert html.count("<ul>") == 1


def test_minimal_valid_report_via_template_manager_no_crash():
    """Minimal-but-model-valid FinancialReport (empty analyses/suggestions) renders safely."""
    report = FinancialReport(
        executive_summary="Résumé minimal.",
        analyses=[],
        suggestions=[],
    )

    html = TemplateManager().render_report(CREW_IDENTIFIER, report.model_dump())

    # Header (using the model's default `title`) + executive summary always present.
    assert "💰 Daily Financial Report" in html
    assert "Résumé minimal." in html

    # Empty analyses/suggestions suppress the corresponding sections entirely.
    assert "Analyse Détaillée" not in html
    assert "Recommandations" not in html
    # No report_date supplied -> no date paragraph.
    assert "📅" not in html


# ---------------------------------------------------------------------------
# Direct FinancialRenderer tests (using the real model's field names)
# ---------------------------------------------------------------------------


def test_root_container_class_attribute_is_correct():
    """The outer container uses create_soup(), producing class="financial-report"."""
    html = FinancialRenderer().render({})
    assert '<div class="financial-report">' in html


def test_nested_tags_have_correct_class_attribute():
    """Nested tags use ``attrs={"class": ...}``, producing correct ``class=`` attributes."""
    html = FinancialRenderer().render({"executive_summary": "x"})
    assert 'class="financial-header"' in html
    assert 'class="executive-summary"' in html
    # The old, broken literal-underscore attribute must never appear.
    assert 'class_="financial-header"' not in html
    assert 'class_="executive-summary"' not in html


def test_header_date_from_report_date_and_absence():
    """`report_date` renders the date line; its absence omits it."""
    html = FinancialRenderer().render({"report_date": "2026-02-02"})
    assert "📅 2026-02-02" in html

    html_no_date = FinancialRenderer().render({})
    assert "📅" not in html_no_date


def test_header_title_fallback_when_absent_or_empty():
    """Missing or empty `title` falls back to the default header text."""
    assert "💰 Rapport Financier" in FinancialRenderer().render({})
    assert "💰 Rapport Financier" in FinancialRenderer().render({"title": ""})
    assert "💰 My Report" in FinancialRenderer().render({"title": "My Report"})


def test_executive_summary_present_and_absent():
    """`executive_summary` renders the section; its absence skips it."""
    html_present = FinancialRenderer().render({"executive_summary": "Primary summary"})
    assert "Primary summary" in html_present
    assert "📋 Résumé Exécutif" in html_present

    html_absent = FinancialRenderer().render({})
    assert "Résumé Exécutif" not in html_absent


def test_analyses_full_fields():
    """`analyses` renders asset_class heading, summary, and details list."""
    html = FinancialRenderer().render(
        {
            "analyses": [
                "ignored-non-dict-item",  # mixed-in non-dict is skipped, not rendered
                {
                    "asset_class": "ETFs",
                    "summary": "Diversification correcte.",
                    "details": ["Detail X", "Detail Y"],
                },
            ]
        }
    )
    assert "🔍 Analyse Détaillée" in html
    assert "ignored-non-dict-item" not in html
    assert "<h4>ETFs</h4>" in html
    assert "Diversification correcte." in html
    assert "<li>Detail X</li>" in html
    assert "<li>Detail Y</li>" in html


def test_analyses_missing_and_non_list_details_skip_ul():
    """Missing `details`, or `details` that isn't a list, both skip the <ul>."""
    html_missing = FinancialRenderer().render({"analyses": [{"asset_class": "Cash", "summary": "Stable."}]})
    assert "<h4>Cash</h4>" in html_missing
    assert "<ul>" not in html_missing

    html_non_list = FinancialRenderer().render(
        {"analyses": [{"asset_class": "Cash", "summary": "Stable.", "details": "not-a-list"}]}
    )
    assert "<ul>" not in html_non_list


def test_analyses_empty_or_non_dict_items_skip_section():
    """An empty list, or a list with no dict items, skips the whole section."""
    assert "Analyse Détaillée" not in FinancialRenderer().render({"analyses": []})
    assert "Analyse Détaillée" not in FinancialRenderer().render({"analyses": ["just a string", 42]})


def test_analyses_absent_entirely_skips_section():
    """No `analyses` at all skips the section."""
    html = FinancialRenderer().render({"executive_summary": "only summary"})
    assert "Analyse Détaillée" not in html


def test_suggestions_partial_fields():
    """Suggestions combine asset_class/suggestion/rationale; missing parts are omitted."""
    html = FinancialRenderer().render(
        {
            "suggestions": [
                "ignored-non-dict-suggestion",  # mixed-in non-dict is skipped
                {"asset_class": "Or", "suggestion": "Acheter", "rationale": "Valeur refuge"},
                {"suggestion": "Vendre sans classe d'actif"},
                {"asset_class": "Actions"},  # neither suggestion nor rationale
            ]
        }
    )
    assert "💡 Recommandations" in html
    assert "[Or] Acheter" in html
    assert "→ Valeur refuge" in html
    assert "<li>Vendre sans classe d'actif</li>" in html
    assert "<li>[Actions] </li>" in html
    assert 'class="recommendations-list"' in html


def test_suggestions_empty_or_absent_skips_section():
    """An empty `suggestions` list, or none at all, skips the section."""
    assert "Recommandations" not in FinancialRenderer().render({"suggestions": []})
    assert "Recommandations" not in FinancialRenderer().render({"executive_summary": "only summary"})


def test_empty_data_renders_header_only_without_crash():
    """Completely empty dict input still renders the (always-present) header, no crash."""
    html = FinancialRenderer().render({})
    assert "💰 Rapport Financier" in html
    assert "Résumé Exécutif" not in html
    assert "Analyse Détaillée" not in html
    assert "Recommandations" not in html
    # The removed key-metrics section must never appear.
    assert "Métriques Clés" not in html
