"""
Factory function for converting PoemJSONOutput to HTML using the universal template system.
"""

from __future__ import annotations

from epic_news.models.crews.poem_report import PoemJSONOutput
from epic_news.utils.html.template_manager import TemplateManager


def poem_to_html(
    poem_output: PoemJSONOutput, theme: str = "", author: str = "Epic News AI", html_file: str | None = None
) -> str:
    """
    Convert a PoemJSONOutput instance to a complete HTML document using the universal template system.

    Args:
        poem_output (PoemJSONOutput): The poem model to render.
        theme (str): The theme or user request for the poem (optional).
        author (str): The author to display (optional).
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """
    # Prepare content_data as expected by TemplateManager
    content_data = {
        "title": poem_output.title,
        "poem": poem_output.poem,
        "theme": theme,
        "author": author,
    }
    template_manager = TemplateManager()
    html = template_manager.render_report("POEM", content_data)
    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
