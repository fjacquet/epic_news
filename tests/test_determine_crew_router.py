"""Table-driven tests for ReceptionFlow.determine_crew router.

These tests verify the routing decision tree without invoking any LLM —
only the pure if/return chain is exercised. Adding a new crew without a
matching router branch will fail the corresponding row.
"""

from __future__ import annotations

import pytest

from epic_news.main import ReceptionFlow
from epic_news.models.content_state import CrewCategories


def _make_flow(selected_crew: str) -> ReceptionFlow:
    """Build a ReceptionFlow with the given selected_crew on its state."""
    flow = ReceptionFlow(user_request="test")
    flow.state.selected_crew = selected_crew
    return flow


@pytest.mark.parametrize(
    ("selected", "expected"),
    [
        ("HOLIDAY_PLANNER", "go_generate_holiday_plan"),
        ("MEETING_PREP", "go_generate_meeting_prep"),
        ("BOOK_SUMMARY", "go_generate_book_summary"),
        ("COOKING", "go_generate_recipe"),
        ("MENU", "go_generate_menu_designer"),
        ("SHOPPING", "go_generate_shopping_advice"),
        ("POEM", "go_generate_poem"),
        ("COMPANY_NEWS", "go_generate_news_company"),
        ("OPEN_SOURCE_INTELLIGENCE", "go_generate_osint"),
        ("RSS", "go_generate_rss_weekly"),
        ("FINDAILY", "go_generate_findaily"),
        ("NEWSDAILY", "go_generate_news_daily"),
        ("SAINT", "go_generate_saint_daily"),
        ("SALES_PROSPECTING", "go_generate_sales_prospecting_report"),
        ("DEEPRESEARCH", "go_generate_deep_research"),
        ("PESTEL", "go_generate_pestel"),
    ],
)
def test_determine_crew_routes_known_categories(selected: str, expected: str) -> None:
    flow = _make_flow(selected)
    assert flow.determine_crew() == expected


@pytest.mark.parametrize("selected", ["", "UNKNOWN", "NOT_A_CREW", "lowercase_pestel"])
def test_determine_crew_falls_back_to_unknown(selected: str) -> None:
    flow = _make_flow(selected)
    assert flow.determine_crew() == "go_unknown"


def test_every_routed_category_is_a_known_crew_category() -> None:
    """Every category we route on must exist in CrewCategories.

    Catches drift between the router and the canonical category list.
    """
    routed = {
        "HOLIDAY_PLANNER",
        "MEETING_PREP",
        "BOOK_SUMMARY",
        "COOKING",
        "MENU",
        "SHOPPING",
        "POEM",
        "COMPANY_NEWS",
        "OPEN_SOURCE_INTELLIGENCE",
        "RSS",
        "FINDAILY",
        "NEWSDAILY",
        "SAINT",
        "SALES_PROSPECTING",
        "DEEPRESEARCH",
        "PESTEL",
    }
    known = set(CrewCategories.to_dict().values())
    missing = routed - known
    assert not missing, f"Router references categories not in CrewCategories: {missing}"
