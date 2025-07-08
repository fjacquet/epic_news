from pydantic import BaseModel

from epic_news.utils.html.template_manager import TemplateManager


def generic_html_factory(report_model: BaseModel, html_file: str, title: str) -> None:
    """
    Converts a Pydantic model to a visually appealing HTML file.

    Args:
        report_model: The Pydantic model containing the report data.
        html_file: The path to the output HTML file.
        title: The title of the report.
    """
    template_manager = TemplateManager()

    # The selected_crew parameter is not available here.
    # I will use a generic name for the crew.
    html_content = template_manager.render_report("GENERIC", report_model.model_dump())

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
