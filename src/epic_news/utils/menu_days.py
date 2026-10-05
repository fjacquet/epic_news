"""Derive the number of days a menu must cover from the user's request."""

import re

DEFAULT_MENU_DAYS = 7
MAX_MENU_DAYS = 7

_NUMBER_WORDS = {
    "un": 1,
    "une": 1,
    "one": 1,
    "deux": 2,
    "two": 2,
    "trois": 3,
    "three": 3,
    "quatre": 4,
    "four": 4,
    "cinq": 5,
    "five": 5,
    "six": 6,
    "sept": 7,
    "seven": 7,
}
_DAY_UNIT = r"(?:jours?|journ[ée]es?|days?)"
_WEEK_UNIT = r"(?:semaines?|weeks?)"
_NUMBER = r"(\d+|" + "|".join(_NUMBER_WORDS) + r")"


def _to_int(token: str) -> int:
    return int(token) if token.isdigit() else _NUMBER_WORDS[token]


def parse_num_days(*texts: str | None) -> int:
    """Return the number of days (1-7) found in the first text that states one, else 7.

    Understands "2 jours", "3 days", "deux jours" and "une semaine"/"1 week" (= 7).
    """
    for text in texts:
        if not text:
            continue
        lowered = text.lower()
        if match := re.search(rf"\b{_NUMBER}\s*-?\s*{_DAY_UNIT}\b", lowered):
            return max(1, min(MAX_MENU_DAYS, _to_int(match.group(1))))
        if re.search(r"\bweek-?\s?ends?\b", lowered):
            return 2
        if re.search(rf"\b{_NUMBER}?\s*{_WEEK_UNIT}\b", lowered):
            return DEFAULT_MENU_DAYS
    return DEFAULT_MENU_DAYS
