from epic_news.app import html_to_markdown


def test_html_to_markdown_extracts_text():
    html = "<h1>Title</h1><p>Hello <b>world</b></p>"
    result = html_to_markdown(html)
    assert "Title" in result
    assert "Hello" in result
    assert "world" in result
    assert "<" not in result  # tags stripped
    assert (
        result == "Title\nHello \nworld"
    )  # exact extracted text (bs4 preserves trailing space in text node)


def test_html_to_markdown_handles_garbage_gracefully():
    # Empty input must not raise and returns an empty string.
    assert html_to_markdown("") == ""
    # Plain text with no tags passes through unchanged.
    assert html_to_markdown("just plain text") == "just plain text"


def test_html_to_markdown_returns_raw_html_on_parse_failure(mocker):
    # If the parser raises, the original HTML is returned unchanged (fallback path).
    mocker.patch("epic_news.app.BeautifulSoup", side_effect=ValueError("boom"))
    raw = "<p>unchanged</p>"
    assert html_to_markdown(raw) == raw
