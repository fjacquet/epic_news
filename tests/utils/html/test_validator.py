import pytest

from epic_news.utils.html.validator import validate_html


@pytest.fixture
def valid_html():
    """Provides a valid HTML string for tests."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Hello, world!</h1>
</body>
</html>"""


def test_validate_html_with_valid_html(valid_html):
    """Test that valid HTML passes validation."""
    assert validate_html(valid_html) is True


@pytest.mark.parametrize(
    "invalid_html, error_message",
    [
        (
            "<html><head><title>Test</title></head></html>",
            "HTML validation failed: Missing required <body> element",
        ),
        (
            "<html><head></head><body>No title</body></html>",
            "HTML validation failed: Missing required <title> element in <head>",
        ),
    ],
)
def test_validate_html_with_missing_tags_raises_error(invalid_html, error_message):
    """Test that HTML with missing required tags raises ValueError."""
    with pytest.raises(ValueError, match=error_message):
        validate_html(invalid_html)


@pytest.mark.parametrize(
    "invalid_html",
    [
        "<html><head><title>Test</title></head></html>",  # Missing body
        "<html><head></head><body>No title</body></html>",  # Missing title
    ],
)
def test_validate_html_with_missing_tags_returns_false(invalid_html):
    """Test that HTML with missing tags returns False when raise_on_error is False."""
    assert validate_html(invalid_html, raise_on_error=False) is False
