"""Every task of a request-driven crew must see the user's request.

A task without it plans blind: the stated preferences and constraints never reach its
agent (e.g. a holiday crew choosing hotels without knowing the traveler's loyalty cards).
"""

import re
from pathlib import Path

import pytest
import yaml

CREWS_DIR = Path(__file__).parents[2] / "src/epic_news/crews"
# All carry the enriched request brief (ContentState.to_crew_inputs): `context` is the brief,
# `constraints` is derived from the preferences for the menu crews.
REQUEST_PLACEHOLDERS = {"user_preferences_and_constraints", "context", "constraints"}

# Run on a schedule with a canned request: there is no free-text request to pass on.
SCHEDULED = {"news_daily", "rss_weekly", "saint_daily", "fin_daily"}
# Read the raw {user_request} before the brief exists: extraction writes it, classify routes on it.
UPSTREAM = {"information_extraction", "classify"}

TASK_FILES = sorted(
    f for f in CREWS_DIR.glob("*/config/tasks.yaml") if f.parents[1].name not in SCHEDULED | UPSTREAM
)


@pytest.mark.parametrize("tasks_yaml", TASK_FILES, ids=lambda f: f.parents[1].name)
def test_every_task_receives_the_request(tasks_yaml: Path):
    tasks = yaml.safe_load(tasks_yaml.read_text(encoding="utf-8"))
    missing = [
        name
        for name, cfg in tasks.items()
        if not REQUEST_PLACEHOLDERS & set(re.findall(r"\{(\w+)\}", cfg["description"]))
    ]
    assert not missing
