"""Tests for string utilities."""

import pytest

from faker import Faker
from epic_news.utils.string_utils import create_topic_slug

fake = Faker()

def test_create_topic_slug():
    # Test that create_topic_slug creates a URL-safe slug from a topic string
    topic = fake.sentence()
    slug = create_topic_slug(topic)
    assert " " not in slug
    assert all(c.isalnum() or c == "-" for c in slug)

