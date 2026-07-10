"""Every renderer must render agent Markdown, and none may emit live HTML.

Crews return structured JSON (`output_pydantic`), but the LLM writes Markdown *inside*
the JSON string fields. A renderer that assigns those strings with `tag.string = ...`
escapes them, shipping literal `**bold**` to the reader. This was fixed across the
renderer suite; these tests keep it fixed.

Rendering agent text as markup is a security boundary: markdown-it runs with
`html=False`, so raw HTML in agent output must stay escaped, never become a live tag.

POEM is deliberately excluded: whitespace and literal characters are the content of a
poem, so its lines must not be reinterpreted as Markdown.
"""

import re

import pytest

from epic_news.utils.html.template_renderers.renderer_factory import RendererFactory

MD = "**bold**"

# Whitespace-significant output; must keep escaping its content.
LITERAL_BY_DESIGN = {"POEM"}

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<SCRIPT>alert(1)</SCRIPT>",
    "<img src=x onerror=alert(1)>",
    "<ImG SrC=x OnErRoR=alert(1)>",
    "<iframe src='evil'></iframe>",
    "<svg onload=alert(1)>",
    "[x](javascript:alert(1))",
]


def _payload() -> dict:
    """A superset of the field names the renderers look for, every string carrying Markdown."""
    leaf = f"Texte {MD} ici"
    item = {
        "title": f"T {MD}",
        "name": f"N {MD}",
        "description": leaf,
        "content": leaf,
        "summary": leaf,
        "value": leaf,
        "details": leaf,
        "text": leaf,
        "url": "https://example.org",
    }
    data: dict = {}
    for key in [
        "executive_summary",
        "summary",
        "content",
        "description",
        "methodology",
        "conclusion",
        "overview",
        "analysis",
        "introduction",
        "body",
        "recommendation",
        "notes",
        "context",
        "poem",
    ]:
        data[key] = leaf
    for key in [
        "key_findings",
        "findings",
        "recommendations",
        "highlights",
        "insights",
        "risks",
        "sources",
        "items",
        "articles",
        "products",
        "ingredients",
        "steps",
        "stanzas",
        "tags",
    ]:
        data[key] = [leaf, leaf]
    for key in [
        "physical_locations",
        "risk_assessment",
        "supply_chain_map",
        "mergers_and_acquisitions_insights",
        "sections",
        "research_sections",
        "results",
        "companies",
        "leads",
        "technologies",
        "platforms",
        "social_profiles",
        "meetings",
        "recipes",
        "dishes",
        "saints",
        "feeds",
        "entries",
        "stocks",
        "assets",
    ]:
        data[key] = [dict(item), dict(item)]
    for key in ["company_name", "title", "topic", "name", "date", "author"]:
        data[key] = f"Nom {MD}"
    data["metrics"] = {"score": leaf, "level": leaf}
    return data


def _visible(html: str) -> str:
    """Strip the raw-JSON debug block: it shows source data verbatim, so `**` belongs there."""
    body = re.sub(r"<details.*?</details>", "", html, flags=re.S)
    return re.sub(r"<pre.*?</pre>", "", body, flags=re.S)


def _renderable_crews() -> list[str]:
    """Crews whose renderer accepts the generic payload shape (others are covered elsewhere)."""
    ok = []
    for crew in sorted(set(RendererFactory.get_supported_crew_types())):
        try:
            RendererFactory.create_renderer(crew).render(_payload())
        except Exception:
            continue
        ok.append(crew)
    return ok


RENDERABLE = _renderable_crews()


def test_the_probe_actually_exercises_the_renderers():
    """Guard the guard: if the payload stops matching, these tests would vacuously pass."""
    assert len(RENDERABLE) >= 15, f"payload only reached {len(RENDERABLE)} renderers"
    assert "POEM" in RENDERABLE, "the negative control must be exercised too"


@pytest.mark.parametrize("crew", [c for c in RENDERABLE if c not in LITERAL_BY_DESIGN])
def test_renderer_does_not_ship_literal_markdown(crew):
    html = RendererFactory.create_renderer(crew).render(_payload())

    assert "**" not in _visible(html), f"{crew} escaped agent Markdown into the page"


@pytest.mark.parametrize("crew", sorted(LITERAL_BY_DESIGN & set(RENDERABLE)))
def test_poem_keeps_its_text_literal(crew):
    """Negative control: poetry is whitespace-significant and must not be re-parsed."""
    html = RendererFactory.create_renderer(crew).render(_payload())

    assert "**" in _visible(html), f"{crew} should render text literally"


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_no_renderer_emits_live_html_from_agent_text(payload):
    """Markdown rendering must not turn agent output into executable markup."""

    def poison(obj):
        if isinstance(obj, str):
            return payload
        if isinstance(obj, list):
            return [poison(i) for i in obj]
        if isinstance(obj, dict):
            return {k: (v if k == "url" else poison(v)) for k, v in obj.items()}
        return obj

    offenders = []
    for crew in RENDERABLE:
        try:
            html = RendererFactory.create_renderer(crew).render(poison(_payload()))
        except Exception:
            continue
        if re.search(r"<(script|iframe|svg)[\s>]", html, re.IGNORECASE):
            offenders.append((crew, "live tag"))
        elif re.search(r"""<a[^>]+href\s*=\s*["']?\s*javascript:""", html, re.IGNORECASE):
            offenders.append((crew, "javascript: anchor"))

    assert not offenders, f"injection for {payload!r}: {offenders}"
