"""Agent-authored Markdown must be rendered, not escaped into the page.

The deep_research agents emit Markdown (**bold**, "- " bullets, links, `code`) inside the
JSON string fields of DeepResearchReport. The renderer used to assign those strings via
`tag.string = ...`, so a real report shipped literal `**Scalabilité**` and `- ` bullets
to the reader.

Rendering Markdown means interpreting agent text as markup, so the escaping tests below
are load-bearing: markdown-it runs with html=False and must never emit a live tag.
"""

import re

import pytest

from epic_news.utils.html.template_renderers.deep_research_renderer import DeepResearchRenderer


@pytest.fixture
def report() -> dict:
    return {
        "title": "Rapport",
        "topic": "crewai",
        "executive_summary": "Un **résumé** avec [un lien](https://example.org/a).",
        "key_findings": ["**Scalabilité** confirmée", "Appeler `crew.kickoff()`"],
        "methodology": "- première étape\n- seconde étape",
        "research_sections": [
            {
                "title": "Analyse",
                "content": "**Théorie**\n\n- point A\n- point B",
                "sources": [
                    {
                        "title": "Source",
                        "url": "https://example.org/src",
                        "source_type": "web",
                        "summary": "**Important** détail",
                    }
                ],
            }
        ],
        "sources_count": 1,
        "report_date": "2026-07-10",
        "confidence_level": "High",
    }


@pytest.fixture
def html(report) -> str:
    return DeepResearchRenderer().render(report)


def test_no_literal_markdown_survives(html):
    assert "**" not in html, "literal bold markers reached the page"
    assert "- point A" not in html, "literal bullet reached the page"


def test_block_markdown_becomes_elements(html):
    assert "<strong>" in html
    assert "<li>" in html and "<ul>" in html


def test_inline_markdown_in_list_items_has_no_nested_paragraph(html):
    """render_markdown_inline is used inside <li>; a nested <p> would be invalid."""
    finding = re.search(r'<li class="finding-item">(.*?)</li>', html, re.S)
    assert finding, "finding item not found"
    assert "<strong>" in finding.group(1)
    assert "<p>" not in finding.group(1)


def test_code_and_links_render(html):
    assert "<code>" in html
    assert 'href="https://example.org/a"' in html


@pytest.mark.parametrize(
    "payload",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<iframe src='evil'></iframe>",
    ],
)
def test_raw_html_from_agent_text_is_escaped_not_executed(payload):
    """Interpreting agent output as Markdown must not open an injection hole."""
    data = {
        "title": "T",
        "executive_summary": payload,
        "key_findings": [payload],
        "methodology": payload,
        "research_sections": [{"title": "S", "content": payload, "sources": []}],
    }

    html = DeepResearchRenderer().render(data)

    assert not re.search(r"<script[\s>]", html), "live <script> tag emitted"
    assert not re.search(r"<img[\s>]", html), "live <img> tag emitted"
    assert not re.search(r"<iframe[\s>]", html), "live <iframe> tag emitted"
    assert "&lt;" in html, "payload was not escaped at all"
