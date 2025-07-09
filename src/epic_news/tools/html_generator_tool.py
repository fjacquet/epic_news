"""
HTML Generator Tool for CrewAI agents to generate HTML reports using TemplateManager.

This tool provides proper CrewAI-compliant access to the unified template system
without bypassing the agent-task architecture.
"""

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from epic_news.utils.directory_utils import ensure_output_directories
from epic_news.utils.html.template_manager import TemplateManager


class HtmlGeneratorToolInput(BaseModel):
    """Input schema for HTML Generator Tool."""

    state_data: str = Field(
        description="Complete state data as JSON string containing crew results and context"
    )
    selected_crew: str = Field(
        description="The crew type (FINDAILY, NEWSDAILY, COOKING, etc.) for contextual HTML generation"
    )
    output_file: str = Field(description="Output file path where the HTML report should be written")


class HtmlGeneratorTool(BaseTool):
    """Tool for generating HTML reports using the unified template system."""

    name: str = "html_generator_tool"
    description: str = (
        "Generate professional HTML reports from crew state data using the unified template system. "
        "This tool handles financial reports, news reports, cooking recipes, and other crew outputs "
        "with proper dark mode support, responsive design, and contextual formatting. "
        "Input should be the complete state data as JSON string and the selected crew type."
    )
    args_schema: type[BaseModel] = HtmlGeneratorToolInput

    def __init__(self):
        """Initialize the HTML Generator Tool with TemplateManager."""
        super().__init__()
        # Initialize template manager without setting as instance attribute to avoid Pydantic validation error
        object.__setattr__(self, "template_manager", TemplateManager())

    def _run(self, state_data: str, selected_crew: str, output_file: str) -> str:
        """Generate HTML report using the unified template system."""
        try:
            # Parse the state data from JSON string
            parsed_state_data = json.loads(state_data)

            # Ensure selected_crew is set in the parsed data
            parsed_state_data["selected_crew"] = selected_crew

            # Use the output file path provided by the flow
            output_file_path = output_file

            # Extract content data using the factory pattern
            from epic_news.utils.content_extractors import ContentExtractorFactory

            content_data = ContentExtractorFactory.extract_content(parsed_state_data, selected_crew)

            # Use template manager to render the report
            html_content = self.template_manager.render_report(selected_crew, content_data)

            # Ensure output directories exist using proper utility
            ensure_output_directories()

            # Write the HTML content to the output file
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            success_message = f"✅ HTML report generated successfully at: {output_file_path}"
            print(success_message)

            return success_message

        except json.JSONDecodeError as e:
            error_msg = f"❌ Error parsing state data JSON: {e}"
            print(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"❌ Error generating HTML report: {e}"
            print(error_msg)
            return error_msg
