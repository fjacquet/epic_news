"""Default RAG configuration for epic_news.

The shape mirrors what ``crewai_tools.RagTool`` expects in 1.x — namely,
``vectordb`` (provider + config) and ``embedding_model`` (provider + config).

Persistence path: crewai-tools 1.x stores chromadb data under
``appdirs.user_data_dir(<project_dir>, "CrewAI")`` by default. Override via the
standard ``CREWAI_STORAGE_DIR`` env var rather than constructing a chromadb
``Settings`` ourselves — pydantic v1↔v2 type validation between chromadb's v1
``Settings`` and crewai's v2 ``ChromaDBConfig`` makes explicit overrides break
at runtime.
"""

import copy
import os
from typing import Any

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

DEFAULT_COLLECTION_NAME = "finwiz"

DEFAULT_RAG_CONFIG: dict[str, Any] = {
    "vectordb": {
        "provider": "chromadb",
        "config": {
            "collection_name": DEFAULT_COLLECTION_NAME,
        },
    },
    "embedding_model": {
        "provider": "openai",
        "config": {
            "model_name": "text-embedding-3-large",
        },
    },
}


def build_rag_tool_kwargs(
    config: dict[str, Any] | None = None,
    collection_suffix: str | None = None,
) -> dict[str, Any]:
    """Translate the project's RAG config into kwargs for ``RagTool(...)``.

    crewai-tools 1.x makes ``collection_name`` a top-level ``RagTool`` arg
    rather than a vectordb config field, so we pop it here.

    Args:
        config: Source config matching the shape of ``DEFAULT_RAG_CONFIG``.
            Defaults to a deep copy of ``DEFAULT_RAG_CONFIG``.
        collection_suffix: When provided, the collection becomes
            ``epic_news-{suffix}`` so each crew gets its own slice.

    Returns:
        A dict suitable for ``RagTool(**kwargs)``.
    """
    src = copy.deepcopy(config if config is not None else DEFAULT_RAG_CONFIG)
    vectordb = src.setdefault("vectordb", {"provider": "chromadb", "config": {}})
    vdb_config: dict[str, Any] = vectordb.setdefault("config", {})

    if collection_suffix:
        vdb_config["collection_name"] = f"epic_news-{collection_suffix}"

    collection_name: str = vdb_config.pop("collection_name", DEFAULT_COLLECTION_NAME)

    return {"config": src, "collection_name": collection_name}
