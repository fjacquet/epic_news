import pytest

from epic_news.utils.html.validator import validate_html


def test_validate_html():
    # Test that validate_html validates HTML correctly
    assert validate_html(
        "<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Test</h1></body></html>"
    )
    with pytest.raises(ValueError):
        validate_html("<h1>Test</h1>")
