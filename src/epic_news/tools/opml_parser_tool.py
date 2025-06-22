import xml.etree.ElementTree as ET

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class OpmlParserToolSchema(BaseModel):
    """Input schema for OpmlParserTool."""
    opml_file_path: str = Field(
        ...,
        description="The absolute path to the OPML file to be parsed."
    )

class OpmlParserTool(BaseTool):
    name: str = "OPML Parser"
    description: str = "Parses an OPML file to extract RSS feed URLs."
    args_schema: type[BaseModel] = OpmlParserToolSchema

    def _run(self, opml_file_path: str) -> list[str]:
        """Parses the OPML file and extracts all xmlUrl attributes."""
        try:
            tree = ET.parse(opml_file_path)
            root = tree.getroot()
            urls = []
            for outline in root.findall('.//outline[@xmlUrl]'):
                url = outline.get('xmlUrl')
                if url:
                    urls.append(url)
            return urls
        except ET.ParseError as e:
            return f"Error parsing XML file: {e}"
        except FileNotFoundError:
            return f"Error: The file was not found at {opml_file_path}"
