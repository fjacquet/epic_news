from typing import Any

from crewai.tools import BaseTool
from crewai_tools import RagTool
from pydantic import BaseModel, Field

from epic_news.rag_config import build_rag_tool_kwargs
from epic_news.tools._json_utils import ensure_json_str


class SaveToRagInput(BaseModel):
    """Input schema for SaveToRagTool."""

    text: str = Field(..., description="Text to store in the vector database")


class SaveToRagTool(BaseTool):
    """Tool that saves arbitrary text into the project's RAG database."""

    name: str = "SaveToRag"
    description: str = "Persist text so it can be retrieved later via the RAG tool."
    args_schema: type[BaseModel] = SaveToRagInput
    rag_tool: Any = None  # Define rag_tool as a field

    def __init__(self, rag_tool: RagTool | None = None) -> None:
        super().__init__()  # type: ignore[call-arg]
        self._rag_tool = rag_tool or RagTool(**build_rag_tool_kwargs(), summarize=True)

    def _run(self, text: str) -> str:
        # crewai-tools 1.x: source is positional; ``add()`` no longer accepts ``source=``.
        try:
            self._rag_tool.add(text, data_type="text")
        except Exception as exc:
            return ensure_json_str({"status": "error", "message": str(exc)})
        return ensure_json_str({"status": "success", "message": "stored"})
