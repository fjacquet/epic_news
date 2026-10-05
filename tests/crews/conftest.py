"""Crew tests need a MODEL for LLMConfig; pytest-env supplies the API keys."""

import os

import pytest
from crewai.project import utils as crewai_project_utils

os.environ.setdefault("MODEL", "openrouter/test/model")


@pytest.fixture(autouse=True)
def _fresh_crewai_memo_cache():
    """Start every crew test with an empty CrewAI memo cache.

    CrewAI memoizes @agent/@task results in one process-wide cache keyed by id(self)
    (crewai/project/utils.py). Once a crew instance is garbage-collected, a new crew
    can get the same id and would be handed the old crew's agents and tasks, which
    makes tests depend on what ran before them.
    """
    crewai_project_utils.cache._cache.clear()
