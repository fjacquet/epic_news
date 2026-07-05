"""Unit tests for BaseRenderer, the abstract base class for all HTML
content renderers.

``BaseRenderer`` cannot be instantiated directly (abstract ``render``), so
these tests define a minimal concrete subclass and exercise its shared
helper methods directly, asserting on the actual HTML structure produced
via BeautifulSoup rather than just "truthiness" of the output.
"""

from bs4 import BeautifulSoup

from epic_news.utils.html.template_renderers.base_renderer import BaseRenderer


class _Concrete(BaseRenderer):
    """Minimal concrete subclass so BaseRenderer's helpers can be tested."""

    def __init__(self):
        pass

    def render(self, data):
        return ""


def _soup_with_div() -> tuple[BeautifulSoup, BeautifulSoup]:
    soup = BeautifulSoup("<div></div>", "html.parser")
    container = soup.find("div")
    return soup, container


# ---------------------------------------------------------------------------
# create_soup
# ---------------------------------------------------------------------------


def test_create_soup_strips_trailing_underscore_from_attr_key():
    renderer = _Concrete()
    soup = renderer.create_soup("div", class_="report-container")
    root = soup.find("div")

    assert root is not None
    # trailing underscore stripped: "class_" -> "class". Note: create_soup
    # sets the attribute via `root[key] = value` (a plain string), not via
    # `tag.attrs["class"] = [...]`, so BeautifulSoup does NOT split it into
    # a multi-valued list here -- it stays a single string attribute.
    assert root.get("class") == "report-container"
    assert "class_" not in root.attrs


def test_create_soup_normal_attr_passed_through_unchanged():
    renderer = _Concrete()
    soup = renderer.create_soup("section", id="main-section")
    root = soup.find("section")

    assert root is not None
    assert root["id"] == "main-section"


def test_create_soup_default_tag_is_div():
    renderer = _Concrete()
    soup = renderer.create_soup()
    assert soup.find("div") is not None


# ---------------------------------------------------------------------------
# add_report_header
# ---------------------------------------------------------------------------


def test_add_report_header_with_subtitle():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.add_report_header(soup, container, "Main Title", subtitle="Acme Corp")

    header = container.find("div", class_="report-header")
    assert header is not None
    h1 = header.find("h1")
    h2 = header.find("h2")
    assert h1 is not None and h1.string == "Main Title"
    assert h2 is not None and h2.string == "Acme Corp"


def test_add_report_header_without_subtitle():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.add_report_header(soup, container, "Only Title")

    header = container.find("div", class_="report-header")
    assert header is not None
    assert header.find("h1").string == "Only Title"
    assert header.find("h2") is None


# ---------------------------------------------------------------------------
# add_raw_json_section
# ---------------------------------------------------------------------------


def test_add_raw_json_section_contains_json_in_details_pre_code():
    renderer = _Concrete()
    soup, container = _soup_with_div()
    data = {"key": "value", "num": 42}

    renderer.add_raw_json_section(soup, container, data)

    details = container.find("details", class_="raw-data")
    assert details is not None
    summary = details.find("summary")
    assert summary is not None and summary.string == "Données brutes"
    pre = details.find("pre")
    code = pre.find("code")
    assert code is not None
    assert '"key": "value"' in code.string
    assert '"num": 42' in code.string


def test_add_raw_json_section_custom_title():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.add_raw_json_section(soup, container, {"a": 1}, title="Debug Data")

    summary = container.find("summary")
    assert summary.string == "Debug Data"


# ---------------------------------------------------------------------------
# add_section_title / create_section
# ---------------------------------------------------------------------------


def test_add_section_title_with_icon():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.add_section_title(soup, container, "My Section", icon="🚀")

    h2 = container.find("h2")
    assert h2 is not None
    assert h2.string == "🚀 My Section"


def test_add_section_title_without_icon():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.add_section_title(soup, container, "My Section")

    h2 = container.find("h2")
    assert h2.string == "My Section"


def test_create_section_with_icon_and_custom_css_class():
    renderer = _Concrete()
    soup, _ = _soup_with_div()

    section = renderer.create_section(soup, "Details", icon="ℹ️", css_class="custom-section")

    assert section.name == "section"
    assert section.get("class") == ["custom-section"]
    assert section.find("h2").string == "ℹ️ Details"


def test_create_section_without_icon_uses_default_css_class():
    renderer = _Concrete()
    soup, _ = _soup_with_div()

    section = renderer.create_section(soup, "Details")

    assert section.get("class") == ["report-section"]
    assert section.find("h2").string == "Details"


# ---------------------------------------------------------------------------
# render_dict_as_cards
# ---------------------------------------------------------------------------


def test_render_dict_as_cards_none_data_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_dict_as_cards(soup, container, None, "Title")

    assert container.find("section") is None
    assert len(container.contents) == 0


def test_render_dict_as_cards_empty_dict_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_dict_as_cards(soup, container, {}, "Title")

    assert container.find("section") is None


def test_render_dict_as_cards_all_value_types():
    renderer = _Concrete()
    soup, container = _soup_with_div()
    data = {
        "list_field": ["a", "b", "c"],
        "dict_field": {"sub_key": "sub_value"},
        "scalar_field": "hello",
        "none_field": None,
    }

    renderer.render_dict_as_cards(soup, container, data, "My Data", icon="📊")

    section = container.find("section", class_="report-section")
    assert section is not None
    assert section.find("h2").string == "📊 My Data"

    cards = section.find_all("div", class_="info-card")
    assert len(cards) == 4

    # list field -> <ul><li>
    list_card = cards[0]
    assert list_card.find("h3").string == "List Field"
    lis = list_card.find_all("li")
    assert [li.string for li in lis] == ["a", "b", "c"]

    # dict field -> <p><strong>Sub Key: </strong>sub_value</p>
    dict_card = cards[1]
    p = dict_card.find("p")
    assert p.find("strong").string == "Sub Key: "
    assert "sub_value" in p.get_text()

    # scalar field -> <p>hello</p>
    scalar_card = cards[2]
    assert scalar_card.find("p").string == "hello"

    # None field -> <p>N/A</p>
    none_card = cards[3]
    assert none_card.find("p").string == "N/A"


# ---------------------------------------------------------------------------
# render_list_as_cards
# ---------------------------------------------------------------------------


def test_render_list_as_cards_none_items_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_list_as_cards(soup, container, None, "Title")

    assert container.find("section") is None


def test_render_list_as_cards_empty_list_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_list_as_cards(soup, container, [], "Title")

    assert container.find("section") is None


def test_render_list_as_cards_with_title_key_present():
    renderer = _Concrete()
    soup, container = _soup_with_div()
    items = [{"name": "Alice", "role": "Engineer"}]

    renderer.render_list_as_cards(soup, container, items, "People", title_key="name")

    section = container.find("section")
    grid = section.find("div", class_="cards-grid")
    card = grid.find("div", class_="info-card")
    assert card.find("h3").string == "Alice"
    # remaining field ("role") rendered, title_key field skipped
    p = card.find("p")
    assert p.find("strong").string == "Role: "
    assert "Engineer" in p.get_text()
    # only one <p> since "name" was the title_key and skipped
    assert len(card.find_all("p")) == 1


def test_render_list_as_cards_without_title_key_uses_first_key():
    renderer = _Concrete()
    soup, container = _soup_with_div()
    items = [{"name": "Bob", "role": "Manager"}]

    renderer.render_list_as_cards(soup, container, items, "People")

    card = container.find("div", class_="info-card")
    # first key ("name") used as title
    assert card.find("h3").string == "Bob"
    p = card.find("p")
    assert p.find("strong").string == "Role: "
    assert "Manager" in p.get_text()


def test_render_list_as_cards_falsy_field_value_renders_na():
    renderer = _Concrete()
    soup, container = _soup_with_div()
    items = [{"name": "Carol", "notes": ""}]

    renderer.render_list_as_cards(soup, container, items, "People", title_key="name")

    card = container.find("div", class_="info-card")
    p = card.find("p")
    assert p.find("strong").string == "Notes: "
    assert "N/A" in p.get_text()


def test_render_list_as_cards_with_empty_item_dict():
    renderer = _Concrete()
    soup, container = _soup_with_div()
    items = [{}]

    renderer.render_list_as_cards(soup, container, items, "Title")

    card = container.find("div", class_="info-card")
    assert card.find("h3").string == "Item"
    # no additional <p> fields since item dict is empty
    assert card.find("p") is None


# ---------------------------------------------------------------------------
# render_text_section
# ---------------------------------------------------------------------------


def test_render_text_section_none_text_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_text_section(soup, container, None, "Title")

    assert container.find("section") is None


def test_render_text_section_empty_text_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_text_section(soup, container, "", "Title")

    assert container.find("section") is None


def test_render_text_section_plain_text_not_markdown():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_text_section(soup, container, "**not bold**", "Notes", as_markdown=False)

    section = container.find("section")
    p = section.find("p")
    assert p is not None
    assert p.string == "**not bold**"
    # not parsed as markdown -> no <strong> produced
    assert section.find("strong") is None


def test_render_text_section_as_markdown_true():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_text_section(soup, container, "**bold text**", "Notes", as_markdown=True)

    section = container.find("section")
    strong = section.find("strong")
    assert strong is not None
    assert strong.get_text() == "bold text"


# ---------------------------------------------------------------------------
# render_markdown_block
# ---------------------------------------------------------------------------


def test_render_markdown_block_none_text_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_markdown_block(container, None)

    assert len(container.contents) == 0


def test_render_markdown_block_empty_text_early_return():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    renderer.render_markdown_block(container, "")

    assert len(container.contents) == 0


def test_render_markdown_block_bold_list_and_table():
    renderer = _Concrete()
    soup, container = _soup_with_div()

    markdown_text = "**bold word**\n\n- item one\n- item two\n\n| Col A | Col B |\n| --- | --- |\n| 1 | 2 |\n"

    renderer.render_markdown_block(container, markdown_text)

    html = str(container)
    assert "<strong>bold word</strong>" in html
    assert "<li>item one</li>" in html
    assert "<li>item two</li>" in html
    assert "<table>" in html
    assert container.find("table") is not None


# ---------------------------------------------------------------------------
# add_section
# ---------------------------------------------------------------------------


def test_add_section_parent_found():
    renderer = _Concrete()
    soup = BeautifulSoup('<div id="root"></div>', "html.parser")

    renderer.add_section(soup, "#root", "p", content="Hello world", id="new-para")

    parent = soup.find("div", id="root")
    p = parent.find("p", id="new-para")
    assert p is not None
    assert p.string == "Hello world"


def test_add_section_parent_not_found_is_noop():
    renderer = _Concrete()
    soup = BeautifulSoup('<div id="root"></div>', "html.parser")

    # selector matches nothing -> should not raise, should not modify soup
    renderer.add_section(soup, "#does-not-exist", "p", content="Hello")

    assert soup.find("p") is None


def test_add_section_no_content_creates_empty_tag():
    renderer = _Concrete()
    soup = BeautifulSoup('<div id="root"></div>', "html.parser")

    renderer.add_section(soup, "#root", "span")

    span = soup.find("span")
    assert span is not None
    assert span.string is None


# ---------------------------------------------------------------------------
# escape_html
# ---------------------------------------------------------------------------


def test_escape_html_escapes_all_special_characters():
    renderer = _Concrete()

    result = renderer.escape_html("""& < > " '""")

    assert result == "&amp; &lt; &gt; &quot; &#x27;"


def test_escape_html_leaves_plain_text_unchanged():
    renderer = _Concrete()

    result = renderer.escape_html("plain text 123")

    assert result == "plain text 123"
