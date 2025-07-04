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


def prepare_email_params(state: Any) -> dict[str, Any]:
    """
    Prepare comprehensive email parameters from the application state.
    This function handles all the email input preparation logic needed for email sending.

    Args:
        state: Application state object containing email-related attributes

    Returns:
        Dictionary of email parameters for PostCrew (recipient_email, subject, body, output_file, attachment_path, etc.)
    """
    import os

    # Calculate subject topic (used in subject line and potentially elsewhere)
    subject_topic = (
        state.extracted_info.main_subject_or_activity
        if hasattr(state, "extracted_info")
        and state.extracted_info
        and hasattr(state.extracted_info, "main_subject_or_activity")
        else "Your Report"
    )

    # Get email body content
    email_body_content = getattr(
        state,
        "final_report",
        "Please find your report attached or view content above if no attachment was generated.",
    )

    # Initialize email inputs with environment-based recipient if available
    # Start with default email, then try available sources in order of priority
    recipient = "sample@example.com"  # Default email address

    # Check for recipient attribute (legacy)
    if hasattr(state, "recipient") and state.recipient:
        recipient = state.recipient

    # Check for sendto attribute (new standard name)
    if hasattr(state, "sendto") and state.sendto:
        recipient = state.sendto

    # Environment variable overrides all other sources if present
    env_recipient = os.environ.get("MAIL")
    if env_recipient:
        recipient = env_recipient

    params = {
        "recipient_email": recipient,
        "subject": f"Your Epic News Report: {subject_topic}",
        "body": str(email_body_content),  # Ensure body is string
        "output_file": getattr(state, "output_file", None) or "",
        "topic": subject_topic,
    }

    # Determine attachment: specific attachment_file takes precedence over output_file
    attachment_to_send = None

    # Check specific attachment file first
    if hasattr(state, "attachment_file") and state.attachment_file and os.path.exists(state.attachment_file):
        attachment_to_send = state.attachment_file

    # Fall back to output file if available
    elif hasattr(state, "output_file") and state.output_file and os.path.exists(state.output_file):
        attachment_to_send = state.output_file

    # Always include attachment_path, even if empty, to satisfy PostCrew's task template
    params["attachment_path"] = attachment_to_send if attachment_to_send else ""

    return params


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
