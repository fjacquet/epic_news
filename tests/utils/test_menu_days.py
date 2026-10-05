"""Tests for parse_num_days."""

import pytest

from epic_news.utils.menu_days import parse_num_days


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2 jours", 2),
        ("3 days", 3),
        ("deux jours", 2),
        ("1 journée", 1),
        ("une semaine", 7),
        ("2 weeks", 7),
        ("10 jours", 7),
        ("0 jour", 1),
        ("menu pour 2 personnes", 7),
        ("", 7),
        (None, 7),
    ],
)
def test_parse_num_days(text, expected):
    assert parse_num_days(text) == expected


def test_first_text_with_a_duration_wins():
    assert parse_num_days(None, "menu de 4 jours") == 4
    assert parse_num_days("2 jours", "menu de 4 jours") == 2
