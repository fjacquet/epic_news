import json
import os
from typing import Any

from loguru import logger

from epic_news.models.rss_models import RssFeeds
from epic_news.models.crews.rss_weekly_report import (
    ArticleSummary,
    FeedDigest,
    RssWeeklyReport,
)
from epic_news.utils.directory_utils import ensure_output_directory
from epic_news.utils.html.rss_weekly_html_factory import rss_weekly_to_html


def generate_rss_weekly_html_report(
    json_file_path: str,
    output_html_path: str,
    report_title: str = "Veille Technologique Hebdomadaire",
) -> None:
    """
    Reads translated RSS data from a JSON file, converts it to a Pydantic model,
    then generates and saves a professional HTML report.

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
                    feed_name=feed_data.feed_title,  # Use the title from the feed
                    articles=articles,
                )
            )

        report_model = RssWeeklyReport(
            title=report_title,
            summary="Un résumé hebdomadaire des dernières nouvelles et articles de vos flux RSS.",
            feeds=report_feeds,
        )

        # Generate the HTML report using the factory
        rss_weekly_to_html(report_model, html_file=output_html_path)
        logger.info(f"✅ HTML report successfully generated at: {output_html_path}")

    except FileNotFoundError:
        logger.error(f"❌ Input JSON file not found: {json_file_path}")
    except json.JSONDecodeError:
        logger.error(f"❌ Invalid JSON format in: {json_file_path}")
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred during HTML generation: {e}")


def prepare_email_params(state: Any) -> dict[str, Any]:
    """
    Prepares the parameters for sending an email based on the application state.

    Args:
        state (Any): The application state object, which should have attributes
                     like `selected_crew`, `user_request`, and `output_file`.

    Returns:
        A dictionary with email parameters including recipient,
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


def setup_crew_output_directory(crew_name: str, base_dir: str = "output") -> str:
    """
    Sets up the output directory for a specific crew.

    Args:
        crew_name: Name of the crew (used for the subdirectory name).
        base_dir: Base output directory, defaults to "output".

    Returns:
        Path to the created output directory.
    """
    output_dir = os.path.join(base_dir, crew_name.lower())
    ensure_output_directory(output_dir)
    logger.info(f"Created output directory: {output_dir}")
    return output_dir
