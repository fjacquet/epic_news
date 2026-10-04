import os
import sysconfig
from pathlib import Path
from unittest.mock import MagicMock

from epic_news.config.mcp_config import MCPConfig, close_mcp, get_mcp_tools_or_empty


def test_wikipedia_mcp_runs_locked_local_install_not_uvx_latest():
    params = MCPConfig.get_wikipedia_mcp()

    assert params.command == str(Path(sysconfig.get_path("scripts")) / "wikipedia-mcp")
    assert "uvx" not in params.command
    assert not any("@latest" in arg for arg in params.args)


def test_wikipedia_mcp_console_script_is_installed():
    command = MCPConfig.get_wikipedia_mcp().command

    assert os.access(command, os.X_OK)


def test_unused_mcp_factories_removed():
    for name in ("get_perplexity_mcp", "get_custom_tools_mcp", "get_all_mcp_servers"):
        assert not hasattr(MCPConfig, name)


class _Crew:
    """Minimal stand-in for a @CrewBase instance with an MCP adapter slot."""

    def __init__(self, adapter=None, get_mcp_tools=None):
        self._mcp_server_adapter = adapter
        if get_mcp_tools is not None:
            self.get_mcp_tools = get_mcp_tools


def test_close_mcp_stops_adapter_and_clears_reference():
    adapter = MagicMock()
    crew = _Crew(adapter)

    close_mcp(crew)

    adapter.stop.assert_called_once()
    assert crew._mcp_server_adapter is None


def test_close_mcp_twice_stops_once():
    adapter = MagicMock()
    crew = _Crew(adapter)

    close_mcp(crew)
    close_mcp(crew)

    adapter.stop.assert_called_once()


def test_close_mcp_without_adapter_is_a_noop():
    close_mcp(_Crew())
    close_mcp(object())  # crew that never declared MCP


def test_close_mcp_swallows_stop_errors():
    adapter = MagicMock()
    adapter.stop.side_effect = RuntimeError("loop already closed")
    crew = _Crew(adapter)

    close_mcp(crew)

    assert crew._mcp_server_adapter is None


def test_failed_mcp_start_is_attempted_once_per_crew():
    get_tools = MagicMock(side_effect=RuntimeError("Failed to initialize MCP Adapter"))
    crew = _Crew(get_mcp_tools=get_tools)

    assert get_mcp_tools_or_empty(crew) == []
    assert get_mcp_tools_or_empty(crew) == []

    get_tools.assert_called_once()


def test_successful_mcp_tools_are_returned():
    tool = MagicMock(name="tool")
    crew = _Crew(get_mcp_tools=MagicMock(return_value=[tool]))

    assert get_mcp_tools_or_empty(crew) == [tool]
