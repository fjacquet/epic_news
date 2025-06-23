"""A tool for processing content from Wikipedia articles."""

from enum import Enum

import wikipedia
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ProcessingAction(str, Enum):
    """Enum for processing actions on a Wikipedia article."""

    EXTRACT_KEY_FACTS = "extract_key_facts"
    SUMMARIZE_FOR_QUERY = "summarize_article_for_query"
    SUMMARIZE_SECTION = "summarize_article_section"


class WikipediaProcessingToolInput(BaseModel):
    """Input model for the WikipediaProcessingTool."""

    title: str = Field(..., description="The title of the Wikipedia article.")
    action: ProcessingAction = Field(..., description="The processing action to perform.")
    query: str | None = Field(None, description="The query to tailor the summary for.")
    section_title: str | None = Field(None, description="The title of the section to summarize.")
    max_length: int = Field(150, description="The maximum length of the summary.")
    count: int = Field(5, description="The number of key facts to extract.")


class WikipediaProcessingTool(BaseTool):
    """
    A tool to process content from a Wikipedia article, such as extracting key facts
    or creating query-specific summaries.
    """

    name: str = "Wikipedia Article Processor"
    description: str = (
        "Processes content from a Wikipedia article (e.g., extracts key facts, creates tailored summaries)."
    )
    args_schema: type[BaseModel] = WikipediaProcessingToolInput

    def _run(
        self,
        title: str,
        action: str,
        query: str | None = None,
        section_title: str | None = None,
        max_length: int = 150,
        count: int = 5,
    ) -> str:
        """Run the tool to process article content."""
        try:
            page = wikipedia.page(title, auto_suggest=True, redirect=True)

            if action == ProcessingAction.EXTRACT_KEY_FACTS:
                return self._extract_key_facts(page, topic_within_article=section_title, count=count)
            if action == ProcessingAction.SUMMARIZE_FOR_QUERY:
                if not query:
                    return "Error: 'query' is required for 'summarize_article_for_query'."
                return self._summarize_article_for_query(page, query, max_length)
            if action == ProcessingAction.SUMMARIZE_SECTION:
                if not section_title:
                    return "Error: 'section_title' is required for 'summarize_article_section'."
                return self._summarize_article_section(page, section_title, max_length)

            return f"Error: Unknown action '{action}'."

        except wikipedia.exceptions.PageError:
            return f"Could not find a Wikipedia page for '{title}'. Please check the spelling."
        except wikipedia.exceptions.DisambiguationError as e:
            options = "\n".join(e.options[:5])
            return f"'{title}' is ambiguous. Did you mean one of these?\n{options}"
        except Exception as e:
            return f"An error occurred while processing the Wikipedia article: {e}"

    def _extract_key_facts(
        self, page: wikipedia.WikipediaPage, topic_within_article: str | None = None, count: int = 5
    ) -> str:
        """Extract key facts from a Wikipedia article, optionally focused on a topic."""
        content = page.summary
        if topic_within_article:
            section_content = page.section(topic_within_article)
            if section_content:
                content = section_content
            else:
                return (
                    f"Warning: Section '{topic_within_article}' not found. Returning facts from main summary."
                )

        sentences = content.replace("\n", " ").split(". ")
        facts = ". ".join(sentences[:count])
        return facts + "." if not facts.endswith(".") else facts

    def _summarize_article_for_query(
        self, page: wikipedia.WikipediaPage, query: str, max_length: int = 150
    ) -> str:
        """Get a summary of a Wikipedia article tailored to a specific query."""
        content = page.content
        paragraphs = content.split("\n")
        relevant_paragraphs = [p for p in paragraphs if query.lower() in p.lower()]

        if not relevant_paragraphs:
            return f"Could not find query '{query}' in article '{page.title}'. Returning general summary instead.\n\n{page.summary}"

        relevant_text = "\n".join(relevant_paragraphs)
        summary = relevant_text[:max_length]
        if len(relevant_text) > max_length:
            summary += "..."
        return summary

    def _summarize_article_section(
        self, page: wikipedia.WikipediaPage, section_title: str, max_length: int = 150
    ) -> str:
        """Get a summary of a specific section of a Wikipedia article."""
        section_content = page.section(section_title)

        if not section_content:
            return f"Section '{section_title}' not found in article '{page.title}'."

        summary = section_content[:max_length]
        if len(section_content) > max_length:
            summary += "..."
        return summary
