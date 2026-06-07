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
    # Non-HTML input must not raise.
    assert isinstance(html_to_markdown(""), str)
