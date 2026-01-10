from typing import Literal

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="after")
    def check_action_requirements(self) -> "WikipediaToolInput":
        """Validate that required fields are present for specific actions."""
        if (
            self.action in ["get_article", "get_links", "get_related_topics", "get_sections", "get_summary"]
            and self.title is None
        ):
            raise ValueError(f"`title` is required for action '{self.action}'")
        if self.action == "search_wikipedia" and self.query is None:
            raise ValueError("`query` is required for action 'search_wikipedia'")
        if self.action == "summarize_article_section" and (self.title is None or self.section_title is None):
            raise ValueError(
                "`title` and `section_title` are required for action 'summarize_article_section'"
            )
        return self
