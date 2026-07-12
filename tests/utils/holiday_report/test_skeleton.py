from epic_news.models.holiday_report import ItinerarySkeleton
from epic_news.utils.holiday_report.skeleton import generate_skeleton


class FakeLLM:
    def __init__(self, reply: str):
        self._reply = reply

    def call(self, messages):
        return self._reply


def test_skeleton_parses_json_day_list():
    reply = (
        '[{"date": "2026-07-16", "label": "Montreux -> Montpellier", "stops": ["Montreux"]},'
        ' {"date": "2026-07-17", "label": "Montpellier", "stops": ["Castries"]}]'
    )
    sk = generate_skeleton("research", "summary", FakeLLM(reply))
    assert isinstance(sk, ItinerarySkeleton)
    assert len(sk.days) == 2
    assert sk.days[0].label.startswith("Montreux")


def test_skeleton_falls_back_on_bad_output():
    sk = generate_skeleton("research", "summary", FakeLLM("not json at all"))
    assert isinstance(sk, ItinerarySkeleton)
    assert len(sk.days) == 1  # deterministic single-day fallback
