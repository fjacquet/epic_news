"""One CrewSpec per crew: metadata only, consistent with the Flow (simplification S4)."""

import inspect
import re

from epic_news.config.routing_guide import routing_categories
from epic_news.crew_registry import CREW_REGISTRY, STANDARD_CREWS
from epic_news.main import ReceptionFlow
from epic_news.models.content_state import ContentState, CrewCategories

EXPECTED_KEYS = {
    "BOOK_SUMMARY",
    "COMPANY_NEWS",
    "COOKING",
    "DEEPRESEARCH",
    "FINDAILY",
    "HOLIDAY_PLANNER",
    "MEETING_PREP",
    "MENU",
    "NEWSDAILY",
    "OPEN_SOURCE_INTELLIGENCE",
    "PESTEL",
    "POEM",
    "RSS",
    "SAINT",
    "SALES_PROSPECTING",
    "SHOPPING",
}


def _router_branches() -> dict[str, str]:
    """selected_crew value -> returned step name, read from determine_crew's source."""
    source = inspect.getsource(ReceptionFlow.determine_crew)
    pairs = re.findall(r'selected_crew == "(\w+)":\s*return "(\w+)"', source)
    return dict(pairs)


def _string_leaves(condition) -> set[str]:
    """Collect every string leaf from a listener condition tree (str | dict | list)."""
    if isinstance(condition, str):
        return {condition}
    if isinstance(condition, dict):
        condition = list(condition.values())
    if isinstance(condition, list | tuple):
        return set().union(*(_string_leaves(item) for item in condition)) if condition else set()
    return set()


def _listened_events() -> set[str]:
    events: set[str] = set()
    for member in vars(ReceptionFlow).values():
        definition = getattr(member, "__flow_method_definition__", None)
        events |= _string_leaves(getattr(definition, "listen", None))
    return events


def test_registry_has_one_spec_per_crew():
    assert set(CREW_REGISTRY) == EXPECTED_KEYS
    for key, spec in CREW_REGISTRY.items():
        assert spec.key == key
        assert spec.title and spec.title.strip() == spec.title
        assert callable(spec.docx_assembler)
        for path in (spec.json_path, spec.docx_path):
            assert path is None or path.startswith("output/")
        assert spec.docx_path is None or spec.docx_path.endswith(".docx")
        assert spec.json_path is None or spec.json_path.endswith(".json")
    assert len({spec.title for spec in CREW_REGISTRY.values()}) == len(CREW_REGISTRY)


def test_standard_crews_have_every_field():
    assert set(STANDARD_CREWS) <= set(CREW_REGISTRY)
    for key in STANDARD_CREWS:
        spec = CREW_REGISTRY[key]
        assert spec.model_cls is not None and spec.json_path and spec.docx_path, key


def test_every_spec_has_a_router_branch_and_a_listener():
    branches = _router_branches()
    events = _listened_events()
    for key in CREW_REGISTRY:
        assert key in branches, f"determine_crew has no branch for {key}"
        assert branches[key] in events, f"no @listen for {branches[key]}"
    assert set(branches) == set(CREW_REGISTRY)


def test_categories_come_from_the_registry():
    expected = {key: key for key in CREW_REGISTRY} | {"UNKNOWN": "UNKNOWN"}
    assert CrewCategories.to_dict() == expected
    assert list(CrewCategories.to_dict()) == sorted(CREW_REGISTRY) + ["UNKNOWN"]
    assert CrewCategories.UNKNOWN == "UNKNOWN"
    assert ContentState().categories == expected


def test_unregistered_key_routes_to_unknown():
    flow = ReceptionFlow(user_request="x")
    flow.state.selected_crew = "NOT_A_CREW"
    assert flow.determine_crew() == "go_unknown"


def test_routing_categories_text_is_unchanged():
    """The classify prompt text (alphabetical, as when built from dir()) must not drift."""
    assert routing_categories() == (
        "BOOK_SUMMARY, COMPANY_NEWS, COOKING, DEEPRESEARCH, FINDAILY, HOLIDAY_PLANNER, "
        "MEETING_PREP, MENU, NEWSDAILY, OPEN_SOURCE_INTELLIGENCE, PESTEL, POEM, RSS, SAINT, "
        "SALES_PROSPECTING, SHOPPING"
    )


def test_standard_crews_are_exactly_the_steps_using_run_standard():
    """STANDARD_CREWS must list the keys main.py passes to _run_standard, no more, no less."""
    source = inspect.getsource(inspect.getmodule(ReceptionFlow))
    used = set(re.findall(r'_run_standard\(\s*CREW_REGISTRY\["(\w+)"\]', source))
    assert used == set(STANDARD_CREWS)
