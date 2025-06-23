from typing import Literal

from pydantic import BaseModel, Field


class WikipediaToolInput(BaseModel):
    """Input model for the WikipediaTool, supporting various actions."""

    action: Literal[
        "extract_key_facts",
        "get_article",
        "get_links",
        "get_related_topics",
        "get_sections",
        "get_summary",
        "search_wikipedia",
        "summarize_article_for_query",
        "summarize_article_section",
    ] = Field(..., description="The action to perform with the Wikipedia tool.")

    # Parameters for various actions
    title: str | None = Field(None, description="The title of the Wikipedia article.")
    query: str | None = Field(None, description="The search query for Wikipedia.")
    section_title: str | None = Field(None, description="The title of a section within a Wikipedia article.")
    topic_within_article: str | None = Field(
        None, description="A specific topic to focus on within an article for fact extraction."
    )
    count: int | None = Field(None, description="The number of facts to extract.")
    limit: int | None = Field(5, description="The maximum number of results to return for searches or lists.")
    max_length: int | None = Field(150, description="The maximum length for summaries.")
