from pydantic import BaseModel, Field


class TavilyToolInput(BaseModel):
    """Input schema for the TavilyTool."""

    query: str = Field(..., description="The search query to be sent to Tavily API.")
