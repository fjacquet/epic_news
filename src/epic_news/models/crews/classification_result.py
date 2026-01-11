"""Pydantic model for classification crew output."""

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Result from the classification crew.

    Contains the selected crew category and confidence level for routing
    user requests to appropriate specialized crews.
    """

    selected_crew: str = Field(
        ...,
        description="The category/crew selected for handling the request. "
        "Must be one of the predefined categories from the classification task.",
    )
    confidence: str = Field(
        default="HIGH",
        description="Confidence level of the classification (HIGH, MEDIUM, LOW).",
    )
    reasoning: str | None = Field(
        None,
        description="Brief explanation of why this category was selected.",
    )
