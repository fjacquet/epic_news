import json
import unittest
from unittest.mock import patch

import wikipedia

from src.epic_news.tools.wikipedia_tool import WikipediaTool


class TestWikipediaTool(unittest.TestCase):
    def setUp(self):
        self.tool = WikipediaTool()

    @patch("wikipedia.search")
    def test_search_wikipedia(self, mock_search):
        mock_search.return_value = ["AI", "Artificial General Intelligence"]
        result = self.tool._run(action="search_wikipedia", query="Artificial Intelligence", limit=2)
        self.assertEqual(result, json.dumps(["AI", "Artificial General Intelligence"]))
        mock_search.assert_called_once_with("Artificial Intelligence", results=2)

    @patch("wikipedia.summary")
    def test_get_summary(self, mock_summary):
        mock_summary.return_value = "Summary of AI."
        result = self.tool._run(action="get_summary", title="Artificial Intelligence")
        self.assertEqual(result, "Summary of AI.")
        mock_summary.assert_called_once_with("Artificial Intelligence", auto_suggest=True)

    @patch("wikipedia.page")
    def test_get_article(self, mock_page):
        mock_page.return_value.content = "Full article of AI."
        result = self.tool._run(action="get_article", title="Artificial Intelligence")
        self.assertEqual(result, "Full article of AI.")
        mock_page.assert_called_once_with("Artificial Intelligence", auto_suggest=True, redirect=True)

    @patch("wikipedia.page")
    def test_get_links(self, mock_page):
        mock_page.return_value.links = ["Machine Learning", "Deep Learning"]
        result = self.tool._run(action="get_links", title="Artificial Intelligence")
        self.assertEqual(result, json.dumps(["Machine Learning", "Deep Learning"]))

    @patch("wikipedia.page")
    def test_get_sections(self, mock_page):
        mock_page.return_value.sections = ["History", "Applications"]
        result = self.tool._run(action="get_sections", title="Artificial Intelligence")
        self.assertEqual(result, json.dumps(["History", "Applications"]))

    @patch("wikipedia.page")
    def test_get_related_topics(self, mock_page):
        mock_page.return_value.links = ["ML", "DL", "NLP"]
        result = self.tool._run(action="get_related_topics", title="AI", limit=2)
        self.assertEqual(result, json.dumps(["ML", "DL"]))

    @patch("wikipedia.page")
    def test_extract_key_facts(self, mock_page):
        mock_page.return_value.summary = "Fact one. Fact two. Fact three."
        result = self.tool._run(action="extract_key_facts", title="AI", count=2)
        self.assertEqual(result, "Fact one. Fact two.")

    @patch("wikipedia.page")
    def test_summarize_article_for_query(self, mock_page):
        mock_page.return_value.content = "The history of AI is vast. AI is a growing field."
        result = self.tool._run(
            action="summarize_article_for_query", title="AI", query="history"
        )
        self.assertIn("history of AI", result)

    @patch("wikipedia.page")
    def test_summarize_article_section(self, mock_page):
        mock_page.return_value.section.return_value = "This is the history section."
        result = self.tool._run(
            action="summarize_article_section", title="AI", section_title="History"
        )
        self.assertEqual(result, "This is the history section.")

    def test_missing_title_error(self):
        result = self.tool._run(action="get_summary")
        self.assertEqual(result, "Error: 'title' is a required parameter for this action.")

    def test_missing_query_error(self):
        result = self.tool._run(action="search_wikipedia")
        self.assertEqual(result, "Error: 'query' is a required parameter for 'search_wikipedia'.")

    @patch("wikipedia.search", side_effect=wikipedia.exceptions.PageError("query"))
    def test_page_error(self, mock_search):
        result = self.tool._run(action="search_wikipedia", query="InvalidQuery")
        self.assertIn("Could not find a Wikipedia page for 'InvalidQuery'", result)

    @patch(
        "wikipedia.search",
        side_effect=wikipedia.exceptions.DisambiguationError(
            "query", ["Option1", "Option2"]
        ),
    )
    def test_disambiguation_error(self, mock_search):
        result = self.tool._run(action="search_wikipedia", query="AmbiguousQuery")
        self.assertIn("'AmbiguousQuery' is ambiguous.", result)
