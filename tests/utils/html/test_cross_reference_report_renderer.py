"""Tests for the Cross-Reference Report HTML renderer.

Covers ``CrossReferenceReportRenderer`` (crew_identifier ``CROSS_REFERENCE_REPORT``
in ``RendererFactory``), rendered end-to-end via
``TemplateManager.render_report`` (matching the style used across this test
suite), plus a couple of direct-renderer calls for branches that are not
reachable through the full template pipeline (see notes below).
"""

from html import escape

import pytest

from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.cross_reference_report_renderer import (
    CrossReferenceReportRenderer,
)


@pytest.fixture
def full_report_data() -> dict:
    """A realistic, fully populated CrossReferenceReport payload.

    Exercises every branch in ``_render_dict``/``_render_list``: nested dict,
    list of scalars, list of dicts, list-of-lists, and a bare scalar value.
    """
    return CrossReferenceReport(
        target="Acme Corp",
        executive_summary="Acme Corp shows suspicious offshore activity across three jurisdictions.",
        detailed_findings={
            "entities": ["Entity Alpha", "Entity Beta"],
            "sources": [
                {"name": "Source One", "reliability": "High"},
                {"name": "Source Two", "reliability": "Medium"},
            ],
            "network": {
                "connections": ["Alice", "Bob"],
                "depth": 2,
            },
            "nested_list_of_lists": [["x", "y"], ["z"]],
            "confidence_score": 0.87,
        },
        confidence_assessment="High confidence with minor caveats",
        information_gaps=[
            "Missing financial records for 2023",
            "Unclear beneficial ownership structure",
        ],
    ).model_dump()


def test_full_report_renders_all_sections(full_report_data):
    """Full data: every section, nested structure, and list item shows up."""
    html = TemplateManager().render_report("CROSS_REFERENCE_REPORT", full_report_data)

    # Overall page structure (universal template wrapper).
    assert "<!DOCTYPE html>" in html
    assert "<h1>Cross-Reference Intelligence Report: Acme Corp</h1>" in html

    # Executive summary / confidence assessment (plain text fields).
    assert "<h2>Executive Summary</h2>" in html
    assert "Acme Corp shows suspicious offshore activity across three jurisdictions." in html
    assert "<h2>Confidence Assessment</h2><p>High confidence with minor caveats</p>" in html

    # Detailed findings section marker.
    assert "<h2>Detailed Findings</h2>" in html

    # Dict keys are humanized via `.replace('_', ' ').title()`.
    assert "<strong>Entities:</strong>" in html
    assert "<strong>Sources:</strong>" in html
    assert "<strong>Network:</strong>" in html
    assert "<strong>Nested List Of Lists:</strong>" in html
    assert "<strong>Confidence Score:</strong>" in html
    assert "<strong>Connections:</strong>" in html

    # List of scalars.
    assert "<li>Entity Alpha</li>" in html
    assert "<li>Entity Beta</li>" in html

    # List of dicts -> nested `_render_dict` per item.
    assert "<strong>Name:</strong> Source One" in html
    assert "<strong>Reliability:</strong> High" in html
    assert "<strong>Name:</strong> Source Two" in html
    assert "<strong>Reliability:</strong> Medium" in html

    # Nested dict -> recursive `_render_dict`.
    assert "<li>Alice</li>" in html
    assert "<li>Bob</li>" in html
    assert "<strong>Depth:</strong> 2" in html

    # List-of-lists -> recursive `_render_list` (elif isinstance(item, list)).
    assert "<li>x</li>" in html
    assert "<li>y</li>" in html
    assert "<li>z</li>" in html

    # Bare scalar value -> `f" {value}"` fallback branch.
    assert "<strong>Confidence Score:</strong> 0.87" in html

    # Information gaps: non-empty list branch.
    assert "<h2>Information Gaps</h2><ul>" in html
    assert "<li>Missing financial records for 2023</li>" in html
    assert "<li>Unclear beneficial ownership structure</li>" in html


def test_minimal_data_uses_defaults_and_empty_state():
    """Empty dict: every field falls back to its default, no crash."""
    html = TemplateManager().render_report("CROSS_REFERENCE_REPORT", {})

    assert "<!DOCTYPE html>" in html
    assert "<h1>Cross-Reference Intelligence Report: N/A</h1>" in html
    assert "<h2>Executive Summary</h2><p>No summary provided.</p>" in html
    # detailed_findings defaults to {} -> _render_dict renders an empty <ul>.
    assert "<h2>Detailed Findings</h2><ul></ul>" in html
    assert "<h2>Confidence Assessment</h2><p>N/A</p>" in html
    # information_gaps defaults to [] -> empty-state branch, not the <ul> branch.
    assert "<h2>Information Gaps</h2><p>No information gaps identified.</p>" in html


def test_partial_data_only_target_and_summary_provided():
    """Only some fields provided: confirms independent per-field fallback."""
    data = {
        "target": "Beta Industries",
        "executive_summary": "Preliminary findings only.",
    }
    html = TemplateManager().render_report("CROSS_REFERENCE_REPORT", data)

    assert "<h1>Cross-Reference Intelligence Report: Beta Industries</h1>" in html
    assert "<h2>Executive Summary</h2><p>Preliminary findings only.</p>" in html
    # confidence_assessment and detailed_findings/information_gaps still default.
    assert "<h2>Confidence Assessment</h2><p>N/A</p>" in html
    assert "<h2>Detailed Findings</h2><ul></ul>" in html
    assert "<h2>Information Gaps</h2><p>No information gaps identified.</p>" in html


def test_single_information_gap_renders_as_list_item():
    """A single-item list still goes through the non-empty <ul> branch."""
    data = {"information_gaps": ["Only one gap identified"]}
    html = TemplateManager().render_report("CROSS_REFERENCE_REPORT", data)

    assert "<h2>Information Gaps</h2><ul><li>Only one gap identified</li></ul>" in html


# --- Direct-renderer tests -------------------------------------------------
# The "invalid data format" guard (`if not isinstance(data, dict)`) cannot be
# reached through `TemplateManager.render_report`: `generate_contextual_title`
# calls `.get(...)` on `content_data` before the renderer is ever invoked, so a
# non-dict payload raises `AttributeError` upstream instead of reaching this
# renderer's own guard. We exercise that branch by calling the renderer class
# directly instead.


@pytest.mark.parametrize("bad_data", [None, "not-a-dict", [1, 2, 3], 42])
def test_invalid_data_format_returns_error_paragraph(bad_data):
    """Non-dict payloads hit the renderer's own type guard directly."""
    renderer = CrossReferenceReportRenderer()

    result = renderer.render(bad_data)

    assert result == "<p>Invalid data format for Cross-Reference Report.</p>"


# --- Stored-XSS regression --------------------------------------------------


def test_data_derived_strings_are_html_escaped():
    """Malicious/markup-laden crew output must be escaped, never injected raw.

    Every data-derived field (target, executive_summary, detailed_findings
    keys/values, confidence_assessment, information_gaps items) is exercised
    with a `<script>` payload, a `<b>` tag, and a bare `&`. The renderer must
    HTML-escape all of them so no raw `<script>`, `<b>`, or unescaped `&`
    reaches the output.
    """
    script_payload = "<script>alert(1)</script>"
    bold_payload = "<b>bold</b>"
    malicious_key = "malicious_key<script>alert(1)</script>"
    renderer = CrossReferenceReportRenderer()

    data = {
        "target": script_payload,
        "executive_summary": f"Summary {script_payload} and {bold_payload} & co",
        "detailed_findings": {
            malicious_key: bold_payload,
            "nested": {script_payload: bold_payload},
            "items": [script_payload, bold_payload, "plain & text"],
        },
        "confidence_assessment": script_payload,
        "information_gaps": [script_payload, "plain & simple gap"],
    }

    html = renderer.render(data)

    # No raw dangerous markup anywhere in the output. Case-insensitive because
    # dict keys additionally go through `.title()` before escaping.
    lowered = html.lower()
    assert "<script>" not in lowered
    assert "</script>" not in lowered
    assert "<b>bold</b>" not in lowered

    # Values are escaped as-is (not title-cased): target, confidence_assessment,
    # information_gaps items, and detailed_findings list items/values.
    assert escape(script_payload) in html
    assert escape(bold_payload) in html

    # Bare `&` is escaped in every context: plain text, list items.
    assert "&amp; co" in html  # executive_summary
    assert "plain &amp; simple gap" in html  # top-level information_gaps item
    assert "plain &amp; text" in html  # nested detailed_findings list item

    # Dict keys (top-level and nested) are escaped too, after the existing
    # `.replace('_', ' ').title()` humanization step.
    expected_malicious_key = escape(malicious_key.replace("_", " ").title())
    expected_nested_key = escape(script_payload.replace("_", " ").title())
    assert expected_malicious_key in html
    assert expected_nested_key in html
