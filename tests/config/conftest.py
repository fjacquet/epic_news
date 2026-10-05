"""CrewAI patches are applied by epic_news.main at run time; config tests apply them explicitly.

Without this, a test of patched behaviour (ReAct forcing, the call wrapper, empty retries)
would pass only when an earlier test happened to import ``epic_news.main``.
"""

import pytest

from epic_news.config.crewai_patches import apply_crewai_patches


@pytest.fixture(autouse=True, scope="session")
def _crewai_patches_applied() -> None:
    apply_crewai_patches()
