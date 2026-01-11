"""Pydantic model for reception crew routing output."""

from pydantic import BaseModel, Field


class RoutingResult(BaseModel):
    """Result from the reception crew routing task.

    Determines which specialized crew should handle a user request
    based on content analysis.
    """

    crew_type: str = Field(
        ...,
        description="The crew type selected for handling the request. "
        "Must be one of: NEWS, POEM, COOKING, UNKNOWN.",
    )
    topic: str = Field(
        ...,
        description="The specific topic extracted from the user request.",
    )
