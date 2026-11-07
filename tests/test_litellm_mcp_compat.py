"""litellm's completion path must import under the mcp version crewai allows (<2).

litellm >= 1.106 imports `mcp.types.CacheableResult` (mcp 2.x only) on every
completion call, so every crew died at the classify step with an ImportError.
"""

import importlib


def test_litellm_completion_path_imports_with_installed_mcp():
    importlib.import_module("litellm.responses.mcp.chat_completions_handler")
