import json
from typing import Any

from crewai.tools import BaseTool
from crewai_tools import RagTool
from pydantic import BaseModel, Field

from epic_news.rag_config import DEFAULT_RAG_CONFIG


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
        self._rag_tool = rag_tool or RagTool(config=DEFAULT_RAG_CONFIG, summarize=True)  # type: ignore[arg-type]

    def _run(self, text: str) -> str:
        self._rag_tool.add(source=text, data_type="text")  # type: ignore[call-arg]
        return json.dumps({"status": "success", "message": "stored"})
