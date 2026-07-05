"""Tests for the FinancialRenderer (crew_identifier: FINDAILY).

FinancialRenderer supports two independent data shapes:

* "new format" -- the actual ``FinancialReport`` Pydantic model fields
  (``executive_summary``, ``analyses``, ``suggestions``, ``report_date``).
* "old format" -- legacy free-form keys (``summary``, ``analysis``,
  ``detailed_analysis``, ``recommendations``, ``advice``, ``date``,
  ``key_metrics``/``metrics``) that do NOT exist on ``FinancialReport`` at
  all and are therefore unreachable when data flows through the real
  ``TemplateManager`` -> ``FinancialReport.model_validate`` -> ``model_dump``
  pipeline (extra/unknown keys are dropped by ``model_dump``, and the model
  has no ``summary``/``analysis``/``recommendations``/``metrics`` fields).

To reach those "old format" branches for coverage we must instantiate
``FinancialRenderer`` directly and feed it hand-built dicts -- exactly as
the renderer's own defensive code expects, but never as real production
data would look coming from the model. This is flagged as a data-key/model
mismatch in the test docstrings below rather than "fixed".

Known renderer bug (NOT fixed here, per instructions): most nested tags are
built with ``soup.new_tag(tag, class_="...")``. BeautifulSoup's ``new_tag``
does NOT special-case a trailing underscore the way ``create_soup`` (in
``BaseRenderer``) does, so these tags literally render as a
``class_="..."`` attribute (with the underscore) instead of ``class="..."``.
Only the outermost container (built via ``create_soup``) gets a correct
``class="financial-report"`` attribute. Tests below assert the *actual*
(broken) output.
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
# Full pipeline tests via TemplateManager (mirrors tests/utils/html style)
# ---------------------------------------------------------------------------


def test_full_report_via_template_manager():
    """Full FinancialReport with multiple analyses/suggestions renders expected content."""
    report = FinancialReport(
        title="Ignored Title",  # renderer never reads `title` -- see mismatch test below
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

    # Header
    assert "💰 Rapport Financier" in html
    assert "📅 2026-07-04" in html

    # Executive summary
    assert "Les marchés ont connu une semaine volatile." in html

    # Analyses (new format)
    assert "Actions" in html
    assert "Les actions technologiques ont surperformé." in html
    assert "NVDA +5%" in html
    assert "AAPL -1%" in html
    assert "Obligations" in html
    assert "Les taux se sont stabilisés." in html

    # Suggestions (new format) combine asset_class/suggestion/rationale
    assert "[Crypto] Acheter du Bitcoin" in html
    assert "→ Momentum haussier confirmé." in html

    # Ignored `title` field must NOT leak into the rendered header
    assert "Ignored Title" not in html

    # Empty details list for the "Obligations" analysis produces no stray <ul>
    # for that section -- but the "Actions" section's details did produce one.
    assert html.count("<ul>") == 1


def test_minimal_valid_report_via_template_manager_no_crash():
    """Minimal-but-model-valid FinancialReport (empty analyses/suggestions) renders safely."""
    report = FinancialReport(
        executive_summary="Résumé minimal.",
        analyses=[],
        suggestions=[],
    )

    html = TemplateManager().render_report(CREW_IDENTIFIER, report.model_dump())

    # Non-trivial HTML: header + executive summary always present.
    assert "💰 Rapport Financier" in html
    assert "Résumé minimal." in html

    # Empty analyses/suggestions must suppress the corresponding sections entirely.
    assert "Analyse Détaillée" not in html
    assert "Recommandations" not in html
    # No report_date supplied -> no date paragraph.
    assert "📅" not in html


# ---------------------------------------------------------------------------
# Direct FinancialRenderer tests targeting branches unreachable through the
# real FinancialReport model (legacy "old format" keys and defensive/dead
# code paths). See module docstring for why these bypass TemplateManager.
# ---------------------------------------------------------------------------


def test_root_container_class_attribute_is_correct():
    """The outer container uses create_soup(), which DOES fix class_ -> class."""
    html = FinancialRenderer().render({})
    assert '<div class="financial-report">' in html


def test_nested_tags_have_broken_class_attribute():
    """Known bug: soup.new_tag(..., class_=...) leaks a literal `class_` attribute.

    Documented, not fixed, per task instructions.
    """
    html = FinancialRenderer().render({"summary": "x"})
    # The broken attribute is present verbatim...
    assert 'class_="financial-header"' in html
    assert 'class_="executive-summary"' in html
    # ...and the correct `class=` attribute is absent for these nested tags.
    assert 'class="financial-header"' not in html
    assert 'class="executive-summary"' not in html


def test_header_date_key_precedence_and_fallback():
    """`date` takes precedence over `report_date`; missing both omits the date line."""
    html_date = FinancialRenderer().render({"date": "2026-01-01", "report_date": "2099-12-31"})
    assert "📅 2026-01-01" in html_date
    assert "2099-12-31" not in html_date

    html_report_date_only = FinancialRenderer().render({"report_date": "2026-02-02"})
    assert "📅 2026-02-02" in html_report_date_only

    html_no_date = FinancialRenderer().render({})
    assert "📅" not in html_no_date


def test_executive_summary_fallback_key_and_absence():
    """`executive_summary` takes precedence over `summary`; absence skips the section."""
    html_primary = FinancialRenderer().render(
        {"executive_summary": "Primary summary", "summary": "Should not appear"}
    )
    assert "Primary summary" in html_primary
    assert "Should not appear" not in html_primary

    html_fallback = FinancialRenderer().render({"summary": "Fallback summary"})
    assert "Fallback summary" in html_fallback
    assert "📋 Résumé Exécutif" in html_fallback

    html_absent = FinancialRenderer().render({})
    assert "Résumé Exécutif" not in html_absent


def test_key_metrics_dict_renders_metric_cards():
    """Metrics dict renders one card per key, with underscore->title-case names."""
    html = FinancialRenderer().render({"key_metrics": {"portfolio_value": "10000 EUR", "risk_score": 7}})
    assert "📊 Métriques Clés" in html
    assert "Portfolio Value" in html
    assert "10000 EUR" in html
    assert "Risk Score" in html
    assert '<p class_="metric-value">7</p>' in html


def test_key_metrics_fallback_key():
    """`metrics` is used when `key_metrics` is absent."""
    html = FinancialRenderer().render({"metrics": {"cash": "500 EUR"}})
    assert "Cash" in html
    assert "500 EUR" in html


def test_key_metrics_truthy_non_dict_silently_produces_no_section():
    """BUG (documented, not fixed): a truthy non-dict `metrics` value renders NOTHING.

    `_add_key_metrics` only appends the section if `metrics_grid.find_all()`
    finds children, which only happens when `metrics` is a dict. A list or
    string value is truthy (passes the initial guard) but produces an empty
    grid, so the whole section -- including its title -- is silently dropped.
    """
    html = FinancialRenderer().render({"metrics": ["not", "a", "dict"]})
    assert "Métriques Clés" not in html

    html_absent = FinancialRenderer().render({})
    assert "Métriques Clés" not in html_absent


def test_analysis_old_format_string():
    """`analysis` as a plain string renders a single paragraph."""
    html = FinancialRenderer().render({"analysis": "Marché haussier sur les actions."})
    assert "🔍 Analyse Détaillée" in html
    assert "Marché haussier sur les actions." in html


def test_analysis_old_format_list_with_key_fallbacks():
    """List-of-dict analysis items support title/category and content/description fallbacks."""
    html = FinancialRenderer().render(
        {
            "analysis": [
                {"title": "Section A", "content": "Content A"},
                {"category": "Section B", "description": "Content B"},
                {},  # no title/content at all -- still produces an (empty) section div
            ]
        }
    )
    assert "Section A" in html
    assert "Content A" in html
    assert "Section B" in html
    assert "Content B" in html
    # 3 analysis-section divs total (including the empty one).
    assert html.count('class_="analysis-section"') == 3


def test_analysis_old_format_detailed_analysis_fallback_key():
    """`detailed_analysis` is used when `analysis` is absent."""
    html = FinancialRenderer().render(
        {"detailed_analysis": [{"title": "From detailed_analysis", "content": "Body"}]}
    )
    assert "From detailed_analysis" in html
    assert "Body" in html


def test_analysis_old_format_non_dict_items_drop_entire_section():
    """BUG (documented, not fixed): a list of non-dict analysis items renders NO section.

    Each non-dict item is skipped (`isinstance(item, dict)` check), so no
    <p>/<div> children ever get added under `analysis_div` besides its own
    <h3> title -- and the final `find_all("p") or find_all("div")` gate then
    fails, dropping the section (including its title) entirely.
    """
    html = FinancialRenderer().render({"analysis": ["just a plain string", 42]})
    assert "Analyse Détaillée" not in html


def test_analysis_new_format_full_fields():
    """`analyses` (new format) renders asset_class heading, summary, and details list."""
    html = FinancialRenderer().render(
        {
            "analyses": [
                {
                    "asset_class": "ETFs",
                    "summary": "Diversification correcte.",
                    "details": ["Detail X", "Detail Y"],
                }
            ]
        }
    )
    assert "<h4>ETFs</h4>" in html
    assert "Diversification correcte." in html
    assert "<li>Detail X</li>" in html
    assert "<li>Detail Y</li>" in html


def test_analysis_new_format_missing_and_non_list_details():
    """Missing `details`, or `details` that isn't a list, both skip the <ul>."""
    html_missing = FinancialRenderer().render({"analyses": [{"asset_class": "Cash", "summary": "Stable."}]})
    assert "<h4>Cash</h4>" in html_missing
    assert "<ul>" not in html_missing

    html_non_list = FinancialRenderer().render(
        {"analyses": [{"asset_class": "Cash", "summary": "Stable.", "details": "not-a-list"}]}
    )
    assert "<ul>" not in html_non_list


def test_analysis_old_and_new_format_combined():
    """Both `analysis` (old) and `analyses` (new) present render both blocks."""
    html = FinancialRenderer().render(
        {
            "analysis": "Old format text.",
            "analyses": [{"asset_class": "Crypto", "summary": "New format summary."}],
        }
    )
    assert "Old format text." in html
    assert "New format summary." in html
    assert "<h4>Crypto</h4>" in html


def test_analysis_absent_entirely_skips_section():
    """No `analysis`, `detailed_analysis`, or `analyses` at all skips the section."""
    html = FinancialRenderer().render({"executive_summary": "only summary"})
    assert "Analyse Détaillée" not in html


def test_recommendations_old_format_string():
    """`recommendations` as a plain string renders a single paragraph."""
    html = FinancialRenderer().render({"recommendations": "Diversifiez votre portefeuille."})
    assert "💡 Recommandations" in html
    assert "Diversifiez votre portefeuille." in html


def test_recommendations_old_format_list_variants():
    """List items: plain string, dict with 'text', dict with 'recommendation', dict with neither."""
    html = FinancialRenderer().render(
        {
            "recommendations": [
                "Plain string advice",
                {"text": "Text-key advice"},
                {"recommendation": "Recommendation-key advice"},
                {"other": "no matching key"},
            ]
        }
    )
    assert "<li>Plain string advice</li>" in html
    assert "<li>Text-key advice</li>" in html
    assert "<li>Recommendation-key advice</li>" in html
    # Neither 'text' nor 'recommendation' present -> falls back to str(dict).
    assert "{'other': 'no matching key'}" in html


def test_recommendations_advice_fallback_key():
    """`advice` is used when `recommendations` is absent."""
    html = FinancialRenderer().render({"advice": ["Advice item"]})
    assert "<li>Advice item</li>" in html


def test_recommendations_new_format_suggestions_partial_fields():
    """Suggestions combine asset_class/suggestion/rationale; missing parts are simply omitted."""
    html = FinancialRenderer().render(
        {
            "suggestions": [
                {"asset_class": "Or", "suggestion": "Acheter", "rationale": "Valeur refuge"},
                {"suggestion": "Vendre sans classe d'actif"},
                {"asset_class": "Actions"},  # neither suggestion nor rationale
            ]
        }
    )
    assert "[Or] Acheter" in html
    assert "→ Valeur refuge" in html
    assert "<li>Vendre sans classe d'actif</li>" in html
    assert "<li>[Actions] </li>" in html


def test_recommendations_old_and_new_format_combined_produce_two_lists():
    """Both `recommendations` and `suggestions` present render two separate <ul> lists."""
    html = FinancialRenderer().render(
        {
            "recommendations": ["Old rec"],
            "suggestions": [{"asset_class": "Crypto", "suggestion": "New sugg"}],
        }
    )
    assert "<li>Old rec</li>" in html
    assert "[Crypto] New sugg" in html
    # Both lists share the same (broken) class attribute.
    assert html.count('class_="recommendations-list"') == 2


def test_recommendations_dict_type_silently_produces_title_only_section():
    """BUG (documented, not fixed): a dict `recommendations` value (neither list nor str)
    still renders the section (because its <h3> title alone satisfies the final
    `rec_div.find_all()` gate), but with no actual recommendation content.
    """
    html = FinancialRenderer().render({"recommendations": {"a": 1}})
    assert "💡 Recommandations" in html
    assert "<ul" not in html
    assert "<li>" not in html


def test_recommendations_absent_entirely_skips_section():
    """No `recommendations`, `advice`, or `suggestions` at all skips the section."""
    html = FinancialRenderer().render({"executive_summary": "only summary"})
    assert "Recommandations" not in html


def test_empty_data_renders_header_only_without_crash():
    """Completely empty dict input still renders the (always-present) header, no crash."""
    html = FinancialRenderer().render({})
    assert "💰 Rapport Financier" in html
    assert "Résumé Exécutif" not in html
    assert "Métriques Clés" not in html
    assert "Analyse Détaillée" not in html
    assert "Recommandations" not in html
