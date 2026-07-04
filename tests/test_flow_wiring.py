"""Wiring contract for ReceptionFlow: no dead listeners, no unroutable categories.

Introspects CrewAI 1.15 flow metadata (__flow_method_definition__) without
running the flow. Zero LLM calls.
"""

from epic_news.main import ReceptionFlow
from epic_news.models.content_state import CrewCategories

# Labels the @router("classify") method can return (mirrors determine_crew).
ROUTER_LABELS = {
    "go_generate_holiday_plan",
    "go_generate_meeting_prep",
    "go_generate_book_summary",
    "go_generate_recipe",
    "go_generate_menu_designer",
    "go_generate_shopping_advice",
    "go_generate_poem",
    "go_generate_news_company",
    "go_generate_osint",
    "go_generate_rss_weekly",
    "go_generate_findaily",
    "go_generate_news_daily",
    "go_generate_saint_daily",
    "go_generate_sales_prospecting_report",
    "go_generate_deep_research",
    "go_generate_pestel",
    "go_unknown",
}


def _flow_methods() -> dict[str, object]:
    """All decorated flow methods on ReceptionFlow, by name."""
    return {
        name: member
        for name, member in vars(ReceptionFlow).items()
        if hasattr(member, "__flow_method_definition__")
    }


def _string_leaves(condition) -> set[str]:
    """Collect every string leaf from a condition tree (str | dict | list)."""
    if condition is None:
        return set()
    if isinstance(condition, str):
        return {condition}
    if isinstance(condition, dict):
        leaves: set[str] = set()
        for value in condition.values():
            leaves |= _string_leaves(value)
        return leaves
    if isinstance(condition, (list, tuple)):
        leaves = set()
        for item in condition:
            leaves |= _string_leaves(item)
        return leaves
    return set()


def test_every_listener_trigger_exists():
    """Each name a listener waits on must be a real method or a router label."""
    methods = _flow_methods()
    known_events = set(methods) | ROUTER_LABELS

    dead: dict[str, set[str]] = {}
    for name, member in methods.items():
        triggers = _string_leaves(member.__flow_method_definition__.listen)
        unknown = {t for t in triggers if t not in known_events and t not in ("AND", "OR")}
        if unknown:
            dead[name] = unknown

    assert not dead, f"Listeners waiting on non-existent events: {dead}"


def test_every_router_label_has_a_listener():
    """Each label determine_crew can emit must trigger at least one listener."""
    methods = _flow_methods()
    all_triggers: set[str] = set()
    for member in methods.values():
        all_triggers |= _string_leaves(member.__flow_method_definition__.listen)

    unhandled = ROUTER_LABELS - all_triggers
    assert not unhandled, f"Router labels nothing listens to: {unhandled}"


def test_every_category_is_routable():
    """Every classifier category except UNKNOWN must have a router branch.

    Guards against categories the classifier can emit that dead-end in
    go_unknown (previously: LEAD_SCORING, LOCATION, POST_ONLY, SHOPPING_ADVISOR).
    """
    flow_source_categories = set(CrewCategories.to_dict().values()) - {"UNKNOWN"}
    # Categories determine_crew actually routes (mirrors its if-chain).
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
    unroutable = flow_source_categories - routed
    assert not unroutable, f"Categories with no router branch: {unroutable}"
