"""Deterministic email delivery through Composio Gmail.

Sending a report is not a reasoning task: the recipient, the report file and the
MIME type are all known before any crew starts. Delegating it to an LLM cost a
production run -- the model replaced the validated recipient with the literal
string ``[EMAIL]``, rewrote the French article "la" in the body as ``[ADDRESS]``,
and invented a ``from_email``. Gmail rejected the address and nothing shipped.
Worse, a tool-less agent still reports ``status="success"``.

This module calls ``GMAIL_SEND_EMAIL`` directly and raises on anything that is
not a delivery confirmed by the API, so ``email_sent`` can never be a guess.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from composio import Composio
from loguru import logger

GMAIL_SEND_EMAIL = "GMAIL_SEND_EMAIL"

# Manual tool execution refuses to run without a pinned toolkit version
# (ToolVersionRequiredError). Overridable so a toolkit bump needs no code change.
DEFAULT_GMAIL_VERSION = "20260702_01"


class EmailDeliveryError(RuntimeError):
    """Raised when Composio did not confirm delivery."""


def _gmail_version() -> str:
    return os.getenv("COMPOSIO_GMAIL_VERSION", DEFAULT_GMAIL_VERSION)


def _upload_root() -> Path:
    """Directory auto-upload is confined to. Reports live here; secrets do not."""
    return Path(os.getenv("EPIC_OUTPUT_DIR", "output")).resolve()


def build_client(api_key: str | None = None) -> Composio:
    """Composio client allowed to upload attachments from the output directory.

    Attachments are local paths. Without ``dangerously_allow_auto_upload_download_files``
    the SDK forwards the path verbatim as an already-uploaded S3 key and Gmail 404s.
    ``file_upload_dirs`` replaces Composio's default allowlist, so auto-upload can
    only ever read files we generated.
    """
    key = api_key or os.getenv("COMPOSIO_API_KEY")
    if not key:
        raise EmailDeliveryError("COMPOSIO_API_KEY is not set; cannot send email.")

    return Composio(
        api_key=key,
        dangerously_allow_auto_upload_download_files=True,
        file_upload_dirs=[str(_upload_root())],
    )


def send_report_email(
    *,
    recipient: str,
    subject: str,
    html_body: str,
    attachment_path: str | Path | None = None,
    user_id: str = "default",
    client: Any | None = None,
) -> dict[str, Any]:
    """Send ``html_body`` to ``recipient``, optionally attaching ``attachment_path``.

    Returns the Composio ``data`` payload on success.

    Raises:
        EmailDeliveryError: on an invalid recipient, an empty body, a missing
            attachment, or any response Composio did not mark successful.
    """
    if not recipient or "@" not in recipient:
        raise EmailDeliveryError(f"Refusing to send: {recipient!r} is not a valid email address")
    if not html_body or not html_body.strip():
        raise EmailDeliveryError("Refusing to send an empty report body")

    arguments: dict[str, Any] = {
        "recipient_email": recipient,
        "subject": subject,
        "body": html_body,
        "is_html": True,
    }

    if attachment_path:
        attachment = Path(attachment_path).resolve()
        if not attachment.is_file():
            raise EmailDeliveryError(f"Attachment does not exist: {attachment}")
        arguments["attachment"] = str(attachment)

    client = client or build_client()
    logger.info(
        "📤 Sending report to {} (attachment={})",
        recipient,
        arguments.get("attachment", "none"),
    )

    response = client.tools.execute(
        GMAIL_SEND_EMAIL,
        arguments=arguments,
        user_id=user_id,
        version=_gmail_version(),
    )

    # execute() returns a plain dict, not an object: getattr(response, "successful")
    # would quietly yield None and turn every delivery into a reported failure.
    if not response.get("successful"):
        raise EmailDeliveryError(response.get("error") or "Composio reported failure without an error")

    logger.info("📨 Email delivered to {}", recipient)
    return response.get("data") or {}
