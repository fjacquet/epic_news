import json
import os
from typing import Any

from crewai.tools import BaseTool
from pyairtable import Table
from pydantic import BaseModel

from src.epic_news.models.airtable_models import AirtableReaderToolInput, AirtableToolInput


class AirtableReaderTool(BaseTool):
    name: str = "airtable_read_records"
    description: str = (
        "A tool for reading all records from a specified Airtable table. "
        "It requires the base ID and table name."
    )
    args_schema: type[BaseModel] = AirtableReaderToolInput

    def _run(self, base_id: str, table_name: str) -> str:
        """Run the Airtable tool to read all records."""
        try:
            api_key = os.getenv("AIRTABLE_API_KEY")
            if not api_key:
                raise ValueError("AIRTABLE_API_KEY environment variable not set.")

            table = Table(api_key, base_id, table_name)
            records = table.all()
            return json.dumps(records)
        except Exception as e:
            return f"Error reading records from Airtable: {e}"


class AirtableTool(BaseTool):
    name: str = "airtable_create_record"
    description: str = (
        "A tool for creating a new record in a specified Airtable table. "
        "It requires the base ID, table name, and the data for the new record."
    )
    args_schema: type[BaseModel] = AirtableToolInput

    def _run(self, base_id: str, table_name: str, data: dict[str, Any]) -> str:
        """Run the Airtable tool to create a new record."""
        try:
            api_key = os.getenv("AIRTABLE_API_KEY")
            if not api_key:
                raise ValueError("AIRTABLE_API_KEY environment variable not set.")

            table = Table(api_key, base_id, table_name)
            response = table.create(data)
            return f"Successfully created record in Airtable: {response['id']}"
        except Exception as e:
            return f"Error creating record in Airtable: {e}"
