"""File reader confined to one directory (``output/`` by default).

Agents that also browse the web must not hold crewai's unscoped ``FileReadTool``:
scraped content could steer them into reading ``.env`` or any other local file.
This tool resolves the requested path (following symlinks) and refuses anything
outside its root.
"""

from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from epic_news.tools._json_utils import ensure_json_str

# Keeps a single read from flooding the agent's context window.
MAX_CHARS = 200_000


class OutputFileReadToolSchema(BaseModel):
    """Input schema for OutputFileReadTool."""

    file_path: str = Field(..., description="Path of the file to read, inside the allowed directory.")


class OutputFileReadTool(BaseTool):
    name: str = "Read an output file"
    description: str = (
        "Reads the text content of a file inside the allowed directory (output/ unless "
        "configured otherwise). Returns JSON with 'content' (and 'truncated' when the "
        "file is larger than the read limit) or 'error'."
    )
    args_schema: type[BaseModel] = OutputFileReadToolSchema
    # Relative to the working directory, like render_and_write_html and HtmlToPdfTool.
    root: str = "output"

    def _run(self, file_path: str) -> str:
        root = Path(self.root).resolve()
        path = Path(file_path).resolve()
        if not path.is_relative_to(root):
            return ensure_json_str({"error": f"Access denied: '{file_path}' is outside {self.root}/"})
        if not path.is_file():
            return ensure_json_str({"error": f"File not found: '{file_path}'"})
        try:
            with path.open(encoding="utf-8", errors="replace") as fh:
                content = fh.read(MAX_CHARS + 1)
        except OSError as exc:
            return ensure_json_str({"error": f"Could not read '{file_path}': {exc}"})
        if len(content) > MAX_CHARS:
            return ensure_json_str({"content": content[:MAX_CHARS], "truncated": True})
        return ensure_json_str({"content": content})
