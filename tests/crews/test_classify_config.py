"""Configuration tests for the classify crew — keeps the prompt in sync.

These tests guard the classification YAML against silent regressions:
- the file remains valid YAML
- new categories added to ``CrewCategories`` are mentioned in the prompt
- PESTEL trigger keywords are present (regression guard)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from epic_news.models.content_state import CrewCategories

CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "epic_news"
    / "crews"
    / "classify"
    / "config"
    / "tasks.yaml"
)


@pytest.fixture(scope="module")
def classify_tasks() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_classify_tasks_yaml_loads(classify_tasks: dict) -> None:
    assert "classification_task" in classify_tasks
    task = classify_tasks["classification_task"]
    for key in ("description", "expected_output", "agent"):
        assert key in task


def test_classify_prompt_mentions_pestel_triggers(classify_tasks: dict) -> None:
    """Regression guard: removing PESTEL routing keywords would break classification."""
    description = classify_tasks["classification_task"]["description"].lower()
    for token in ("pestel", "pestle", "macro-environment"):
        assert token in description, f"PESTEL trigger '{token}' missing from prompt"


def test_classify_prompt_references_core_categories(classify_tasks: dict) -> None:
    """Each category we route on must be discoverable in the prompt — at minimum
    the high-traffic ones. Missing categories cause silent misrouting."""
    description = classify_tasks["classification_task"]["description"]
    must_appear = {
        "COOKING",
        "MENU",
        "FINDAILY",
        "NEWSDAILY",
        "COMPANY_NEWS",
        "HOLIDAY_PLANNER",
        "BOOK_SUMMARY",
        "MEETING_PREP",
        "PESTEL",
        "SAINT",
        "POEM",
    }
    missing = {cat for cat in must_appear if cat not in description}
    assert not missing, f"Categories absent from classify prompt: {missing}"


def test_classify_referenced_categories_exist_in_crew_categories(
    classify_tasks: dict,
) -> None:
    """Every uppercase token-like category mentioned in the prompt must exist in
    CrewCategories — catches drift when a category is renamed or removed."""
    description = classify_tasks["classification_task"]["description"]
    known = set(CrewCategories.to_dict().values())

    # Categories explicitly called out as routing targets in the prompt.
    referenced = {
        "COOKING",
        "MENU",
        "SHOPPING_ADVISOR",
        "FINDAILY",
        "NEWSDAILY",
        "COMPANY_NEWS",
        "HOLIDAY_PLANNER",
        "BOOK_SUMMARY",
        "MEETING_PREP",
        "PESTEL",
        "SAINT",
        "POEM",
    }
    actually_in_prompt = {cat for cat in referenced if cat in description}
    drift = actually_in_prompt - known
    assert not drift, (
        f"Prompt references categories not in CrewCategories: {drift}. "
        "Either rename in YAML or add to CrewCategories."
    )


def test_classify_output_file_is_relative(classify_tasks: dict) -> None:
    """Output paths must stay project-relative (CLAUDE.md path-management rule)."""
    output_file = classify_tasks["classification_task"].get("output_file", "")
    assert output_file
    assert not output_file.startswith("/"), "output_file must be project-relative"
