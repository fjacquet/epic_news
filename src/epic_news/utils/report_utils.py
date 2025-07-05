"""Utilities for report generation, content extraction, and file operations."""

import json
import logging
import os
from typing import Any

from epic_news.models.rss_models import RssFeeds
from epic_news.models.rss_weekly_models import (
    ArticleSummary,
    FeedDigest,
    RssWeeklyReport,
)
from epic_news.utils.directory_utils import ensure_output_directory
from epic_news.utils.html.rss_weekly_html_factory import rss_weekly_to_html

logger = logging.getLogger(__name__)


def get_final_report_content(state: Any) -> str | None:
    """
    Retrieves the final report content from the application state.

    Args:
        state: Application state object containing report attributes

    Returns:
        The content of the final report as a string, or None if no report is found
    """
    # List of possible attribute names where report content might be stored
    report_attributes = [
        "cross_reference_report",
        "osint_report",
        "company_profile",
        "tech_stack",
        "web_presence_report",
        "hr_intelligence_report",
        "legal_analysis_report",
        "geospatial_analysis_report",
        "holiday_plan",
        "marketing_report",
        "recipe",
        "book_summary",
        "poem",
        "news_report",
        "sales_prospecting_report",
        "meeting_prep_report",
        "shopping_advice_report",
        "rss_weekly_report",
        "fin_daily_report",
        "news_daily_report",
        "saint_daily_report",
    ]

    for attr in report_attributes:
        content = getattr(state, attr, None)
        if content:
            logger.info(f"Found final report content in 'state.{attr}'")
            return str(content)

    logger.warning("No final report content found in any of the expected state attributes.")
    return None


def write_output_to_file(content: str | None, output_file: str | None) -> bool:
    """
    Writes content to the specified output file.

    Args:
        content: Content to write to the file
        output_file: Path to the output file

    Returns:
        True if the write operation was successful, False otherwise
    """
    if not output_file:
        logger.warning("No output file path provided. Skipping file write.")
        return False

    if not content:
        logger.warning("No content to write. Skipping file write.")
        return False

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Successfully wrote content to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error writing to file {output_file}: {str(e)}")
        return False


"""
This module provides utility functions for generating and handling reports.
"""

import json
from loguru import logger
from typing import Any, Dict

from bs4 import BeautifulSoup

# Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def generate_rss_weekly_html_report(json_file_path: str, output_html_path: str):
    """
    Generates an HTML report from a JSON file containing RSS feed data.

    Args:
        json_file_path (str): The path to the input JSON file.
        output_html_path (str): The path to the output HTML file.
    """
    logger.info(f"Generating HTML report from {json_file_path}...")

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found: {json_file_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in {json_file_path}")
        return

    soup = BeautifulSoup(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly RSS Summary</title>
            <style>
                body { font-family: sans-serif; line-height: 1.6; margin: 20px; }
                h1, h2 { color: #333; }
                .feed { margin-bottom: 30px; }
                .article { margin-bottom: 15px; }
                .article-title { font-size: 1.2em; font-weight: bold; }
                .article-summary { margin-top: 5px; }
            </style>
        </head>
        <body>
            <h1>Weekly RSS Summary</h1>
        </body>
        </html>
    """,
        "html.parser",
    )

    body = soup.body

    for feed in data.get("rss_feeds", []):
        feed_div = soup.new_tag("div", **{"class": "feed"})
        feed_title = soup.new_tag("h2")
        feed_title.string = feed.get("feed_title", "Untitled Feed")
        feed_div.append(feed_title)

        for article in feed.get("articles", []):
            article_div = soup.new_tag("div", **{"class": "article"})
            article_title_div = soup.new_tag("div", **{"class": "article-title"})
            article_link = soup.new_tag("a", href=article.get("link", "#"))
            article_link.string = article.get("title", "Untitled Article")
            article_title_div.append(article_link)
            article_div.append(article_title_div)

            if "summary" in article:
                summary_p = soup.new_tag("p", **{"class": "article-summary"})
                summary_p.string = article["summary"]
                article_div.append(summary_p)

            feed_div.append(article_div)

        body.append(feed_div)

    try:
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        logger.info(f"HTML report successfully generated at {output_html_path}")
    except IOError as e:
        logger.error(f"Failed to write HTML report: {e}")


def prepare_email_params(state: Any) -> Dict[str, Any]:
    """
    Prepares the parameters for sending an email based on the application state.

    Args:
        state (Any): The application state object, which should have attributes
                     like `selected_crew`, `user_request`, and `output_file`.

    Returns:
        Dict[str, Any]: A dictionary with email parameters including recipient,
                        subject, body, and attachment path.
    """
    recipient = "test-ia@fjaquet.fr"
    subject = f"Epic News Report: {state.selected_crew} - {state.user_request}"
    body = f"Please find the report for '{state.user_request}' attached."
    attachment_path = getattr(state, "output_file", None)

    return {
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "attachment_path": attachment_path,
    }


if __name__ == "__main__":
    # Example usage of generate_rss_weekly_html_report
    sample_data = {
        "rss_feeds": [
            {
                "feed_title": "Tech News",
                "articles": [
                    {
                        "title": "AI Breakthroughs",
                        "link": "http://example.com/ai",
                        "summary": "New AI models are changing the game.",
                    }
                ],
            }
        ]
    }
    json_path = "output/reports/sample_rss_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)

    generate_rss_weekly_html_report(json_path, "output/reports/sample_rss_report.html")

    # Example usage of prepare_email_params
    class MockState:
        def __init__(self):
            self.selected_crew = "NEWS"
            self.user_request = "Latest on space exploration"
            self.output_file = "output/reports/space_report.html"

    mock_state = MockState()
    email_params = prepare_email_params(mock_state)
    print("Prepared email parameters:", email_params)



def generate_rss_weekly_html_report(
    json_file_path: str,
    output_html_path: str,
    report_title: str = "Veille Technologique Hebdomadaire",
) -> None:
    """
    Reads translated RSS data from a JSON file, converts it to an HTML report,
    and saves the report.

    Args:
        json_file_path: Path to the input JSON file (e.g., 'final-report.json').
        output_html_path: Path to save the output HTML file.
        report_title: The title for the HTML report.
    """
    logger.info(f"🚀 Generating HTML report from {json_file_path}...")

    try:
        with open(json_file_path, encoding="utf-8") as f:
            data = json.load(f)

        rss_feeds_model = RssFeeds.model_validate(data)

        # Transform RssFeeds to RssWeeklyReport
        report_feeds = []
        total_articles = 0
        for feed_data in rss_feeds_model.rss_feeds:
            articles = [
                ArticleSummary(
                    title=a.title,
                    link=a.link,
                    published=a.published if a.published else "",
                    summary=a.content or a.summary or "",
                    source_feed=feed_data.feed_url,
                )
                for a in feed_data.articles
            ]
            report_feeds.append(
                FeedDigest(
                    feed_url=feed_data.feed_url,
                    feed_name="",  # Factory will generate one from the URL
                    articles=articles,
                    total_articles=len(articles),
                )
            )
            total_articles += len(articles)

        report_model = RssWeeklyReport(
            title=report_title,
            summary="Un résumé hebdomadaire des dernières nouvelles et articles de vos flux RSS.",
            feeds=report_feeds,
            total_feeds=len(report_feeds),
            total_articles=total_articles,
        )

        # Generate the HTML report
        rss_weekly_to_html(report_model, html_file=output_html_path)
        logger.info(f"✅ HTML report successfully generated at: {output_html_path}")

    except Exception as e:
        logger.error(f"❌ Error during HTML generation: {e}")


def setup_crew_output_directory(crew_name: str, base_dir: str = "output") -> str:
    """
    Sets up the output directory for a specific crew.

    Args:
        crew_name: Name of the crew (used for the subdirectory name)
        base_dir: Base output directory, defaults to "output"

    Returns:
        Path to the created output directory
    """
    output_dir = os.path.join(base_dir, crew_name.lower())
    ensure_output_directory(output_dir)
    logger.info(f"Created output directory: {output_dir}")
    return output_dir
