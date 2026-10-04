"""Wikipedia MCP tools come from CrewBase's managed adapter, not a hand-rolled one.

``@CrewBase`` lazily starts one ``MCPServerAdapter`` per crew instance from
``mcp_server_params`` and stops it in an after-kickoff hook. These tests pin that
wiring with a fake adapter (no subprocess) and check that a server that cannot
start degrades to "no Wikipedia tools" instead of failing the crew build.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from epic_news.config.mcp_config import MCPConfig
from epic_news.crews.deep_research.deep_research import DeepResearchCrew
from epic_news.crews.pestel.pestel_crew import PestelCrew

MCP_CREWS = [DeepResearchCrew, PestelCrew]


def _fake_adapter_cls():
    adapter = MagicMock(name="adapter")
    adapter.tools.filter_by_names.return_value = []
    return MagicMock(name="MCPServerAdapter", return_value=adapter), adapter


@pytest.mark.parametrize("crew_cls", MCP_CREWS, ids=lambda c: c.__name__)
def test_declares_wikipedia_mcp_server_params(crew_cls):
    assert crew_cls.mcp_server_params == MCPConfig.get_wikipedia_mcp()


@pytest.mark.parametrize("crew_cls", MCP_CREWS, ids=lambda c: c.__name__)
def test_adapter_started_once_and_stopped_after_kickoff(crew_cls):
    adapter_cls, adapter = _fake_adapter_cls()
    with patch("crewai_tools.MCPServerAdapter", adapter_cls):
        crew = crew_cls().crew()

    adapter_cls.assert_called_once()  # one shared adapter for every agent
    adapter.stop.assert_not_called()

    output = object()
    for callback in crew.after_kickoff_callbacks:
        output = callback(output)

    adapter.stop.assert_called_once()


@pytest.mark.parametrize("crew_cls", MCP_CREWS, ids=lambda c: c.__name__)
def test_unavailable_mcp_server_degrades_to_no_wikipedia_tools(crew_cls):
    failing = MagicMock(side_effect=RuntimeError("Failed to initialize MCP Adapter"))
    with patch("crewai_tools.MCPServerAdapter", failing):
        crew = crew_cls().crew()

    tool_names = {t.name for a in crew.agents for t in a.tools or []}
    assert not {"search", "fetch"} & tool_names
    assert crew.agents, "crew still builds without the MCP server"


@pytest.mark.parametrize("crew_cls", MCP_CREWS, ids=lambda c: c.__name__)
def test_no_hand_rolled_adapter_lifecycle(crew_cls):
    for attr in ("wikipedia_tools", "_wikipedia_mcp", "close"):
        assert not hasattr(crew_cls, attr), f"{crew_cls.__name__}.{attr} should be gone"
