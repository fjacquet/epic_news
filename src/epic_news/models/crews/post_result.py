"""Pydantic model for post crew distribution output."""

from pydantic import BaseModel, Field


class PostResult(BaseModel):
    """Result from the post crew email distribution task.

    Contains details about the email delivery attempt including
    status, recipients, and any errors encountered.
    """

    status: str = Field(
        ...,
        description="Delivery status: 'success' or 'failure'.",
    )
    recipient_email: str = Field(
        ...,
        description="Email address of the recipient.",
    )
    subject: str = Field(
        ...,
        description="Subject line of the sent email.",
    )
    html_preserved: bool = Field(
        default=False,
        description="Whether HTML content was preserved in the email body.",
    )
    language_preserved: bool = Field(
        default=False,
        description="Whether original language was maintained (not translated).",
    )
    attachment_sent: bool = Field(
        default=False,
        description="Whether an attachment was successfully sent.",
    )
    attachment_path_provided: str = Field(
        default="N/A",
        description="Path to the attachment if provided, otherwise 'N/A'.",
    )
    attachment_filename: str = Field(
        default="N/A",
        description="Filename of the attachment if sent, otherwise 'N/A'.",
    )
    error_message: str = Field(
        default="None",
        description="Error details if delivery failed, otherwise 'None'.",
    )
