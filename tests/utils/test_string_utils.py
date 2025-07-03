"""Tests for string utilities."""

import pytest

from epic_news.utils.string_utils import create_topic_slug


@pytest.mark.parametrize(
    "topic, expected_slug",
    [
        ("Tarte aux pommes", "tarte-aux-pommes"),
        ("Crème brûlée", "creme-brulee"),
        ("  Spaces before and after  ", "spaces-before-and-after"),
        ("Special!@#$Chars", "specialchars"),
        ("Multiple---dashes and   spaces", "multiple-dashes-and-spaces"),
        ("A topic with numbers 123", "a-topic-with-numbers-123"),
        ("", ""),
        ("---", ""),
    ],
)
def test_create_topic_slug(topic, expected_slug):
    """Test that create_topic_slug correctly converts topics to slugs."""
    assert create_topic_slug(topic) == expected_slug
