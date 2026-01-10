"""A tool for fetching content from Wikipedia articles."""

import json
from enum import Enum

import wikipedia
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ArticleAction(str, Enum):
    """Enum for actions that can be performed on a Wikipedia article."""

    GET_SUMMARY = "get_summary"
    GET_ARTICLE = "get_article"
    GET_LINKS = "get_links"
    GET_SECTIONS = "get_sections"
    GET_RELATED_TOPICS = "get_related_topics"


class WikipediaArticleToolInput(BaseModel):
    """Input model for the WikipediaArticleTool."""

    title: str = Field(..., description="The title of the Wikipedia article.")
    action: ArticleAction = Field(..., description="The action to perform on the article.")
    limit: int = Field(default=10, description="Limit for actions like 'get_related_topics'.")


class WikipediaArticleTool(BaseTool):
    """
    A tool to fetch various types of content from a Wikipedia article.
    Actions include getting a summary, full content, links, sections, or related topics.
    """

    name: str = "Wikipedia Article Fetcher"
    description: str = (
        "Fetches content (summary, full article, links, etc.) from a specified Wikipedia article."
    )
    args_schema: type[BaseModel] = WikipediaArticleToolInput

    def _run(self, title: str, action: str, limit: int = 10) -> str:
        """Run the tool to fetch article content."""
        try:
            page = wikipedia.page(title, auto_suggest=True, redirect=True)

            if action == ArticleAction.GET_SUMMARY:
                return str(page.summary)
            if action == ArticleAction.GET_ARTICLE:
                return str(page.content)
            if action == ArticleAction.GET_LINKS:
                return json.dumps(page.links)
            if action == ArticleAction.GET_SECTIONS:
                return json.dumps(page.sections)
            if action == ArticleAction.GET_RELATED_TOPICS:
                return json.dumps(page.links[:limit])

            return f"Error: Unknown action '{action}'."

        except wikipedia.exceptions.PageError:
            return f"Could not find a Wikipedia page for '{title}'. Please check the spelling."
        except wikipedia.exceptions.DisambiguationError as e:
            options = "\n".join(e.options[:5])
            return f"'{title}' is ambiguous. Did you mean one of these?\n{options}"
        except Exception as e:
            return f"An error occurred while fetching the Wikipedia article: {e}"
