from typing import Any, Dict

from pydantic import BaseModel, Field


class AirtableToolInput(BaseModel):
    """Input schema for the AirtableTool."""

    base_id: str = Field(..., description="The ID of the Airtable base.")
    table_name: str = Field(..., description="The name of the table within the base.")
    data: Dict[str, Any] = Field(..., description="The data to be added to the table as a dictionary.")
