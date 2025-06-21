import os
from typing import Type, Dict, Any

from crewai.tools import BaseTool
from pydantic import BaseModel
from pyairtable import Table

from src.epic_news.models.airtable_models import AirtableToolInput


class AirtableTool(BaseTool):
    name: str = "airtable_create_record"
    description: str = (
        "A tool for creating a new record in a specified Airtable table. "
        "It requires the base ID, table name, and the data for the new record."
    )
    args_schema: Type[BaseModel] = AirtableToolInput

    def _run(self, base_id: str, table_name: str, data: Dict[str, Any]) -> str:
        """Run the Airtable tool to create a new record."""
        try:
            api_key = os.getenv('AIRTABLE_API_KEY')
            if not api_key:
                raise ValueError("AIRTABLE_API_KEY environment variable not set.")

            table = Table(api_key, base_id, table_name)
            response = table.create(data)
            return f"Successfully created record in Airtable: {response['id']}"
        except Exception as e:
            return f"Error creating record in Airtable: {e}"
