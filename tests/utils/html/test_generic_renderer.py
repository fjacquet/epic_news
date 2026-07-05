"""Unit tests for GenericRenderer, the fallback renderer used for crew types
without a specialized renderer.

These tests target the real rendering logic in
``src/epic_news/utils/html/template_renderers/generic_renderer.py``:
header generation, common free-text fields, list-of-scalars and
list-of-dicts sections (including falsy-value filtering), the raw-data
debug section (with its per-type formatting branches), and empty-state
handling.
"""

from bs4 import BeautifulSoup

from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.generic_renderer import GenericRenderer


def _render(data: dict, crew_type: str = "UNKNOWN") -> str:
    return GenericRenderer().render(data, crew_type=crew_type)


def test_empty_data_renders_only_header():
    """Empty dict: header is always added, but content and raw-data sections
    are skipped (`_add_content_sections` appends nothing, `_add_raw_data`
    returns early on falsy `data`)."""
    html = _render({})

    assert "Rapport UNKNOWN" in html
    assert "generic-report" in html  # outer container class (correctly rendered)
    assert "generic-content" not in html
    assert "raw-data-section" not in html


def test_common_fields_render_as_content_sections_and_whitespace_field_is_skipped():
    """Flat dict hitting the `common_fields` loop: title/summary/content/text
    become `<h3>`+`<p>` sections. A whitespace-only string fails the
    `value.strip()` truthiness check and must be skipped from content, even
    though it still appears verbatim in the raw-data dump. A non-string
    `title` (int) also must be skipped from content (isinstance check)."""
    data = {
        "title": "Mon Titre",
        "summary": "Un resume.",
        "content": "Contenu principal",
        "description": "   ",  # whitespace-only -> must be excluded from content
        "text": "Texte libre",
    }
    html = _render(data, crew_type="TESTCREW")

    assert "Rapport TESTCREW" in html

    for heading, value in [
        ("Title", "Mon Titre"),
        ("Summary", "Un resume."),
        ("Content", "Contenu principal"),
        ("Text", "Texte libre"),
    ]:
        assert f"<h3>{heading}</h3>" in html
        assert value in html

    # whitespace-only description must not produce a content section
    assert "<h3>Description</h3>" not in html
    # but the raw value (including the spaces) still shows up in the raw dump
    # (format is f"{key}: {value}" -> "description" + ": " + "   " = 4 spaces)
    assert "description:    \n" in html


def test_non_string_common_field_excluded_from_content_section():
    """A common-field key whose value is not a string (e.g. an int) fails the
    `isinstance(value, str)` check and must not produce a content section,
    even though it is truthy."""
    html = _render({"title": 123})

    assert "<h3>Title</h3>" not in html
    # still present in the raw-data dump, formatted as a plain scalar
    assert "title: 123" in html


def test_list_of_scalars_creates_list_section_with_separate_items():
    """A list value (of any key) creates a `list-section` with one `<li>`
    per item, title-cased from the key name."""
    data = {"tags": ["python", "testing", "html"]}
    html = _render(data)

    assert "<h3>Tags</h3>" in html
    soup = BeautifulSoup(html, "html.parser")
    items = [li.get_text() for li in soup.find_all("li")]
    assert items == ["python", "testing", "html"]

    # raw-data section summarizes the list by length, not by content
    assert "tags: [3 items]" in html


def test_list_of_dicts_joins_truthy_fields_and_filters_falsy_values():
    """Each dict item in a list is flattened to a `k: v` joined string; the
    join expression `if v` drops falsy values (empty string, 0) from the
    line, item order and key order otherwise preserved."""
    data = {
        "items": [
            {"name": "Widget", "price": 10, "note": ""},
            {"name": "Gadget", "count": 0, "color": "red"},
        ]
    }
    html = _render(data)

    assert "<h3>Items</h3>" in html
    soup = BeautifulSoup(html, "html.parser")
    items = [li.get_text() for li in soup.find_all("li")]
    assert items == ["name: Widget, price: 10", "name: Gadget, color: red"]

    # falsy fields must not leak into the rendered line
    assert "note:" not in html
    assert "count: 0" not in html

    assert "items: [2 items]" in html


def test_empty_list_excluded_from_content_but_present_in_raw_data():
    """`if isinstance(value, list) and value` means an empty list must not
    create a list-section, but `_add_raw_data` still summarizes it (since
    the outer `data` dict itself is non-empty/truthy)."""
    html = _render({"empty_list": []})

    assert "Empty List" not in html
    assert "list-section" not in html
    assert "empty_list: [0 items]" in html


def test_raw_data_section_formats_every_type_branch():
    """Exercises every branch of `_add_raw_data`'s per-type formatting:
    scalar (str/int/float/bool), list (`[n items]`), dict (`{n fields}`),
    and the fallback `type(value).__name__` branch for anything else
    (here: None -> 'NoneType')."""
    data = {
        "score": 42,
        "ratio": 3.14,
        "flag": True,
        "tags": ["a", "b"],
        "meta": {"x": 1, "y": 2},
        "extra": None,
    }
    html = _render(data)

    for line in [
        "score: 42",
        "ratio: 3.14",
        "flag: True",
        "tags: [2 items]",
        "meta: {2 fields}",
        "extra: NoneType",
    ]:
        assert line in html

    # the list value also gets its own content list-section (dual rendering)
    assert "<h3>Tags</h3>" in html


def test_via_template_manager_generic_identifier_uses_generic_renderer():
    """End-to-end: TemplateManager.render_report('GENERIC', ...) must route
    through RendererFactory -> GenericRenderer (registered explicitly in
    `_RENDERER_MAP`) and produce the full page with real content embedded."""
    data = {"summary": "Resume general de test."}
    html = TemplateManager().render_report("GENERIC", data)

    assert "Resume general de test." in html
    assert "generic-report" in html
    # page-level title uses the crew identifier passed to render_report...
    assert "Rapport GENERIC" in html
    # ...but the renderer's own body header always uses the default
    # crew_type ("UNKNOWN"), since RendererFactory/TemplateManager never
    # forward `selected_crew` into `renderer.render(...)`.
    assert "Rapport UNKNOWN" in html


def test_via_template_manager_unmapped_identifier_falls_back_to_generic():
    """An identifier with no entry in `RendererFactory._RENDERER_MAP` must
    still fall back to GenericRenderer (`.get(crew_type, GenericRenderer)`)."""
    data = {"content": "Contenu de secours."}
    html = TemplateManager().render_report("SOME_TOTALLY_UNKNOWN_CREW", data)

    assert "Contenu de secours." in html
    assert "generic-report" in html


def test_child_tags_use_real_class_attribute():
    """Child divs built with `soup.new_tag("div", attrs={"class": "..."})`
    must render a real `class="..."` attribute (not a literal `class_="..."`),
    same as the outer container (built via `create_soup`)."""
    html = _render({"summary": "x"})

    # outer container: class handled correctly by create_soup()
    assert 'class="generic-report"' in html

    # child divs: real class attribute, no literal class_= anywhere
    assert 'class="generic-header"' in html
    assert 'class="generic-content"' in html
    assert 'class="content-section"' in html
    assert 'class="raw-data-section"' in html
    assert "class_=" not in html

    # and, as a consequence, BeautifulSoup DOES expose these divs under a
    # real "class" attribute, findable via the standard bs4 search API
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("div", class_="generic-header") is not None
