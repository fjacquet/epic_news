import os

from epic_news.rag_config import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_RAG_CONFIG,
    PROJECT_ROOT,
    build_rag_tool_kwargs,
)


def test_default_rag_config_structure():
    """Verify the structure matches crewai-tools 1.x ``RagToolConfig``."""
    assert set(DEFAULT_RAG_CONFIG.keys()) == {"vectordb", "embedding_model"}

    vectordb = DEFAULT_RAG_CONFIG["vectordb"]
    assert vectordb["provider"] == "chromadb"
    assert vectordb["config"]["collection_name"] == DEFAULT_COLLECTION_NAME

    embed = DEFAULT_RAG_CONFIG["embedding_model"]
    assert embed["provider"] == "openai"
    assert isinstance(embed["config"]["model_name"], str)


def test_project_root_path():
    """Ensure the PROJECT_ROOT path is correctly calculated and points to the project root."""
    assert os.path.exists(os.path.join(PROJECT_ROOT, "pyproject.toml"))


def test_build_rag_tool_kwargs_default():
    """Default build promotes ``collection_name`` to the top-level kwarg."""
    kwargs = build_rag_tool_kwargs()
    assert kwargs["collection_name"] == DEFAULT_COLLECTION_NAME

    vdb_config = kwargs["config"]["vectordb"]["config"]
    assert "collection_name" not in vdb_config  # promoted to top-level kwarg


def test_build_rag_tool_kwargs_with_suffix():
    """Suffix produces a crew-scoped collection name without mutating the source config."""
    kwargs = build_rag_tool_kwargs(collection_suffix="stocks")
    assert kwargs["collection_name"] == "epic_news-stocks"

    # Source config remains pristine.
    assert DEFAULT_RAG_CONFIG["vectordb"]["config"]["collection_name"] == DEFAULT_COLLECTION_NAME
