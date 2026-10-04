import json

from epic_news.utils.holiday_report.assemble import _day_slices

_RESEARCH = {
    "itinerary_metadata": {"title": "Florence"},
    "essential_booking_timeline": [{"milestone": "a"}, {"milestone": "b"}],
    "daily_itineraries": [{"day_number": 1, "theme": "Duomo"}, {"day_number": 2, "theme": "Uffizi"}],
}


def test_slices_per_day_from_fenced_json():
    raw = "```json\n" + json.dumps(_RESEARCH) + "\n```"
    slices = _day_slices(raw, 2)
    assert [json.loads(s)["theme"] for s in slices] == ["Duomo", "Uffizi"]


def test_prefers_list_whose_key_mentions_day():
    slices = _day_slices(json.dumps(_RESEARCH), 2)
    assert json.loads(slices[0])["day_number"] == 1


def test_no_match_when_day_count_differs():
    assert _day_slices(json.dumps(_RESEARCH), 3) is None


def test_not_json_returns_none():
    assert _day_slices("Jour 1: Duomo. Jour 2: Uffizi.", 2) is None


def test_nested_day_list_is_found():
    nested = {"plan": {"days": [{"d": 1}, {"d": 2}, {"d": 3}]}}
    assert len(_day_slices(json.dumps(nested), 3)) == 3
