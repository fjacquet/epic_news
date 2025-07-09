from contextlib import contextmanager


@contextmanager
def mock_knowledge_base_dependencies(mocker):
    """A context manager to mock all dependencies for the knowledge base script."""
    mocks = {
        "update": mocker.patch("scripts.update_knowledge_base.update_market_data"),
        "prune": mocker.patch("scripts.update_knowledge_base.prune_outdated_knowledge"),
        "yf_ticker": mocker.patch("scripts.update_knowledge_base.yf.Ticker"),
        "rag_tool": mocker.patch("scripts.update_knowledge_base.RagTool"),
        "save_tool": mocker.patch("scripts.update_knowledge_base.SaveToRagTool"),
        "logger": mocker.patch("scripts.update_knowledge_base.logger"),
    }
    try:
        yield mocks
    finally:
        # No need for explicit teardown, mocker handles it automatically
        pass


@contextmanager
def mock_knowledge_base_dependencies_no_logger(mocker):
    """A context manager to mock dependencies but leave logger unmocked for caplog tests."""
    mocks = {
        "yf_ticker": mocker.patch("scripts.update_knowledge_base.yf.Ticker"),
        "rag_tool": mocker.patch("scripts.update_knowledge_base.RagTool"),
        "save_tool": mocker.patch("scripts.update_knowledge_base.SaveToRagTool"),
    }
    try:
        yield mocks
    finally:
        # No need for explicit teardown, mocker handles it automatically
        pass
