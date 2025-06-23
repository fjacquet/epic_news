import json
from typing import Optional

import wikipedia
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.wikipedia_models import WikipediaToolInput


class WikipediaTool(BaseTool):
    name: str = "wikipedia_tool"
    description: str = "A comprehensive tool to interact with Wikipedia. It can search, fetch, and summarize articles and their sections."
    args_schema: type[BaseModel] = WikipediaToolInput

    def _run(self, **kwargs) -> str:
        """Run the Wikipedia tool with the specified action and arguments."""
        action = kwargs.get("action")

        try:
            if action == "search_wikipedia":
                return self._search_wikipedia(
                    query=kwargs.get("query"), limit=kwargs.get("limit")
                )

            title = kwargs.get("title")
            if not title:
                return "Error: 'title' is a required parameter for this action."

            if action == "get_summary":
                return self._get_summary(title=title)
            elif action == "get_article":
                return self._get_article(title=title)
            elif action == "get_links":
                return self._get_links(title=title)
            elif action == "get_sections":
                return self._get_sections(title=title)
            elif action == "get_related_topics":
                return self._get_related_topics(title=title, limit=kwargs.get("limit"))
            elif action == "extract_key_facts":
                return self._extract_key_facts(
                    title=title,
                    topic_within_article=kwargs.get("topic_within_article"),
                    count=kwargs.get("count", 5),
                )
            elif action == "summarize_article_for_query":
                return self._summarize_article_for_query(
                    title=title,
                    query=kwargs.get("query"),
                    max_length=kwargs.get("max_length", 150),
                )
            elif action == "summarize_article_section":
                return self._summarize_article_section(
                    title=title,
                    section_title=kwargs.get("section_title"),
                    max_length=kwargs.get("max_length", 150),
                )
            else:
                return f"Error: Unknown action '{action}'."

        except wikipedia.exceptions.PageError:
            page_identifier = kwargs.get("title") or kwargs.get("query")
            return f"Could not find a Wikipedia page for '{page_identifier}'. Please check the spelling or try a different query."
        except wikipedia.exceptions.DisambiguationError as e:
            page_identifier = kwargs.get("title") or kwargs.get("query")
            options = "\n".join(e.options[:5])
            return f"'{page_identifier}' is ambiguous. Did you mean one of these?\n{options}"
        except Exception as e:
            return f"An error occurred while using the Wikipedia tool: {e}"

    def _search_wikipedia(self, query: str, limit: int = 5) -> str:
        """Search Wikipedia for articles matching a query."""
        if not query:
            return "Error: 'query' is a required parameter for 'search_wikipedia'."
        results = wikipedia.search(query, results=limit)
        return json.dumps(results)

    def _get_summary(self, title: str) -> str:
        """Get a summary of a Wikipedia article."""
        return wikipedia.summary(title, auto_suggest=True)

    def _get_article(self, title: str) -> str:
        """Get the full content of a Wikipedia article."""
        page = wikipedia.page(title, auto_suggest=True, redirect=True)
        return page.content

    def _get_links(self, title: str) -> str:
        """Get the links contained within a Wikipedia article."""
        page = wikipedia.page(title, auto_suggest=True, redirect=True)
        return json.dumps(page.links)

    def _get_sections(self, title: str) -> str:
        """Get the sections of a Wikipedia article."""
        page = wikipedia.page(title, auto_suggest=True, redirect=True)
        return json.dumps(page.sections)

    def _get_related_topics(self, title: str, limit: int = 10) -> str:
        """Get topics related to a Wikipedia article based on its links."""
        page = wikipedia.page(title, auto_suggest=True, redirect=True)
        return json.dumps(page.links[:limit])

    def _extract_key_facts(
        self, title: str, topic_within_article: Optional[str] = None, count: int = 5
    ) -> str:
        """Extract key facts from a Wikipedia article, optionally focused on a topic."""
        page = wikipedia.page(title, auto_suggest=True, redirect=True)
        content = page.summary
        if topic_within_article:
            section_content = page.section(topic_within_article)
            if section_content:
                content = section_content
            else:
                return f"Warning: Section '{topic_within_article}' not found. Returning facts from main summary."

        # A simple implementation: return the first 'count' sentences.
        sentences = content.replace("\n", " ").split(". ")
        facts = ". ".join(sentences[:count])
        return facts + "." if not facts.endswith(".") else facts

    def _summarize_article_for_query(
        self, title: str, query: str, max_length: int = 150
    ) -> str:
        """Get a summary of a Wikipedia article tailored to a specific query."""
        if not query:
            return "Error: 'query' is a required parameter for 'summarize_article_for_query'."
        page = wikipedia.page(title, auto_suggest=True, redirect=True)
        content = page.content
        paragraphs = content.split("\n")
        relevant_paragraphs = [p for p in paragraphs if query.lower() in p.lower()]

        if not relevant_paragraphs:
            return f"Could not find query '{query}' in article '{title}'. Returning general summary instead.\n\n{page.summary}"

        relevant_text = "\n".join(relevant_paragraphs)
        summary = relevant_text[:max_length]
        if len(relevant_text) > max_length:
            summary += "..."
        return summary

    def _summarize_article_section(
        self, title: str, section_title: str, max_length: int = 150
    ) -> str:
        """Get a summary of a specific section of a Wikipedia article."""
        if not section_title:
            return "Error: 'section_title' is a required parameter for 'summarize_article_section'."
        page = wikipedia.page(title, auto_suggest=True, redirect=True)
        section_content = page.section(section_title)

        if not section_content:
            return f"Section '{section_title}' not found in article '{title}'."

        summary = section_content[:max_length]
        if len(section_content) > max_length:
            summary += "..."
        return summary


if __name__ == "__main__":
    # Example usage of the WikipediaTool
    tool = WikipediaTool()

    # 1. Search for a topic
    print("--- 1. Searching for 'Deep Learning' ---")
    search_results = tool._run(action="search_wikipedia", query="Deep Learning", limit=3)
    print(search_results)
    print("\n")

    # 2. Get the summary of an article
    print("--- 2. Getting summary for 'Artificial intelligence' ---")
    summary_result = tool._run(action="get_summary", title="Artificial intelligence")
    print(summary_result)
    print("\n")

    # 3. Get the full article content
    # print("--- 3. Getting full article for 'Python (programming language)' ---")
    # article_result = tool._run(action="get_article", title="Python (programming language)")
    # print(article_result[:500] + "...") # Print first 500 chars
    # print("\n")

    # 4. Extract key facts from a specific section
    print("--- 4. Extracting key facts from 'Albert Einstein' ---")
    facts_result = tool._run(
        action="extract_key_facts",
        title="Albert Einstein",
        topic_within_article="Annus Mirabilis papers",
        count=2,
    )
    print(facts_result)
    print("\n")

    # 5. Summarize an article for a specific query
    print("--- 5. Summarizing 'World War II' for query 'D-Day' ---")
    query_summary_result = tool._run(
        action="summarize_article_for_query",
        title="World War II",
        query="D-Day",
        max_length=250,
    )
    print(query_summary_result)
    print("\n")

    # 6. Handle a page not found error
    print("--- 6. Handling a non-existent page ---")
    error_result = tool._run(action="get_summary", title="NonExistentPageAbc123")
    print(error_result)
    print("\n")
