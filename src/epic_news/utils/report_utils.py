import html
import json
import re
from typing import Any

from loguru import logger
from pydantic import ValidationError

from epic_news.models.content_state import FALLBACK_EMAIL
from epic_news.models.crews.rss_weekly_report import (
    ArticleSummary,
    FeedDigest,
    RssWeeklyReport,
)
from epic_news.models.rss_models import RssFeeds


def _transform_rss_feeds_to_report(rss_feeds_model: RssFeeds, report_title: str) -> RssWeeklyReport:
    """Convert a low-level RssFeeds payload into the RssWeeklyReport renderer model."""
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
            FeedDigest(  # type: ignore[call-arg]
                feed_url=feed_data.feed_url,
                feed_name=getattr(feed_data, "feed_title", None)
                or getattr(feed_data, "feed_name", "Unknown"),
                articles=articles,
            )
        )
    return RssWeeklyReport(  # type: ignore[call-arg]
        title=report_title,
        summary="Un résumé hebdomadaire des dernières nouvelles et articles de vos flux RSS.",
        feeds=report_feeds,
    )


def load_rss_weekly_report(
    json_file_path: str, report_title: str = "Veille Technologique Hebdomadaire"
) -> RssWeeklyReport:
    """Load a translated RSS JSON file into an RssWeeklyReport.

    Accepts either RssWeeklyReport-shaped JSON (used directly) or RssFeeds-shaped
    JSON (transformed via _transform_rss_feeds_to_report). Raises on validation
    errors matching neither shape.
    """
    with open(json_file_path, encoding="utf-8") as f:
        data = json.load(f)

    try:
        report_model = RssWeeklyReport.model_validate(data)
        logger.info("✅ Data already in RssWeeklyReport shape, using directly")
    except ValidationError as e_direct:
        logger.info("Data not in RssWeeklyReport shape; trying RssFeeds + transform")
        try:
            rss_feeds_model = RssFeeds.model_validate(data)
        except ValidationError as e_feeds:
            logger.error(
                "❌ JSON matches neither RssWeeklyReport nor RssFeeds.\n"
                "  RssWeeklyReport errors: {}\n"
                "  RssFeeds errors: {}",
                e_direct,
                e_feeds,
            )
            raise
        report_model = _transform_rss_feeds_to_report(rss_feeds_model, report_title)

    return report_model


# Guaranteed-valid final fallback so a missing/empty/typo'd MAIL env var never
# hard-fails the send with a confusing "invalid recipient". Shares the single
# literal with content_state (no drift) but stays independent of MAIL: a malformed
# non-empty MAIL taints DEFAULT_EMAIL, so the fallback must be the bare constant,
# not DEFAULT_EMAIL.
_FALLBACK_RECIPIENT = FALLBACK_EMAIL
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_email(value: Any) -> str | None:
    """Return the trimmed address if it looks like a valid email, else None."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if _EMAIL_RE.match(value) else None


def prepare_email_params(state: Any) -> dict[str, Any]:
    """
    Prepares the parameters for sending an email based on the application state.

    Args:
        state (Any): The application state object, which should have attributes
                     like `selected_crew`, `user_request`, `sendto`, and `output_file`.

    Returns:
        A dictionary with email parameters including recipient,
        subject, body, and attachment path.
    """
    # The recipient is driven entirely by the MAIL env var (ContentState.sendto
    # defaults to DEFAULT_EMAIL = os.getenv("MAIL") or ...). A getattr default is
    # dead code because the field always exists, so a missing/empty/malformed MAIL
    # would otherwise reach the email tool and fail with a confusing "invalid
    # recipient". Validate and fall back to a known-good address instead.
    raw_sendto = getattr(state, "sendto", None)
    recipient = _valid_email(raw_sendto)
    if recipient is None:
        # Log only the failure category, never the raw value — an invalid recipient
        # can be user-supplied and would otherwise persist an email address (PII).
        reason = "empty" if not (isinstance(raw_sendto, str) and raw_sendto.strip()) else "malformed"
        logger.warning(
            "✉️  Email recipient from state.sendto/MAIL is {} (value not logged); "
            "using fallback. Set a valid MAIL env var to control it.",
            reason,
        )
        recipient = _FALLBACK_RECIPIENT
    subject = f"Epic News Report: {state.selected_crew} - {state.user_request}"
    # The sender posts the body as HTML, so the user request must be escaped.
    body = f"Please find the report for '{html.escape(str(state.user_request))}' attached."
    attachment_path = getattr(state, "output_file", None)
    topic = f"{state.selected_crew} - {state.user_request}"

    return {
        "recipient_email": recipient,
        "subject": subject,
        "body": body,
        "attachment_path": attachment_path,
        "topic": topic,
    }
