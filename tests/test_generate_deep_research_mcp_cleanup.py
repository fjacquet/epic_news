"""generate_deep_research must stop the crew's Wikipedia MCP server even if kickoff fails.

CrewBase's own close hook only runs after a successful kickoff.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from epic_news import main as main_module
from epic_news.main import ReceptionFlow


def test_generate_deep_research_closes_mcp_when_kickoff_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    closed: list = []
    seen: list = []

    class _StubDeepResearchCrew:
        pass

    def _failing_kickoff(crew, _inputs):
        seen.append(crew)
        raise RuntimeError("provider down")

    monkeypatch.setattr(main_module, "DeepResearchCrew", _StubDeepResearchCrew)
    monkeypatch.setattr(main_module, "kickoff_flow", _failing_kickoff)
    monkeypatch.setattr(main_module, "close_mcp", closed.append)

    with pytest.raises(RuntimeError, match="provider down"):
        ReceptionFlow(user_request="deep research on CrewAI").generate_deep_research()

    assert len(seen) == 1
    assert closed == seen
