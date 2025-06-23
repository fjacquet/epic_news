import os

from epic_news.rag_config import DEFAULT_RAG_CONFIG, PROJECT_ROOT


def test_default_rag_config_structure():
    """Verify the structure and basic types of the RAG configuration."""
    assert "llm" in DEFAULT_RAG_CONFIG
    assert "embedder" in DEFAULT_RAG_CONFIG
    assert "vectordb" in DEFAULT_RAG_CONFIG
    assert "chunker" in DEFAULT_RAG_CONFIG

    assert "provider" in DEFAULT_RAG_CONFIG["llm"]
    assert "config" in DEFAULT_RAG_CONFIG["llm"]

    assert "provider" in DEFAULT_RAG_CONFIG["embedder"]
    assert "config" in DEFAULT_RAG_CONFIG["embedder"]

    assert "provider" in DEFAULT_RAG_CONFIG["vectordb"]
    assert "config" in DEFAULT_RAG_CONFIG["vectordb"]
    assert "dir" in DEFAULT_RAG_CONFIG["vectordb"]["config"]
    assert isinstance(DEFAULT_RAG_CONFIG["vectordb"]["config"]["dir"], str)

    assert "chunk_size" in DEFAULT_RAG_CONFIG["chunker"]
    assert isinstance(DEFAULT_RAG_CONFIG["chunker"]["chunk_size"], int)


def test_project_root_path():
    """Ensure the PROJECT_ROOT path is correctly calculated and points to the project root."""
    # Check if a known file/directory at the root exists relative to PROJECT_ROOT
    assert os.path.exists(os.path.join(PROJECT_ROOT, "pyproject.toml"))
