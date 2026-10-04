import os
import sysconfig
from pathlib import Path

from epic_news.config.mcp_config import MCPConfig


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
