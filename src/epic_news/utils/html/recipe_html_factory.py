"""
Factory function for converting PaprikaRecipe to HTML using the universal template system.
"""

from __future__ import annotations

from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils.html.template_manager import TemplateManager


def recipe_to_html(recipe_data: PaprikaRecipe, html_file: str | None = None) -> str:
    """
    Convert a PaprikaRecipe instance to a complete HTML document using the universal template system.

    Args:
        recipe_data (PaprikaRecipe): The recipe data model to render.
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """
    # Prepare content_data as expected by TemplateManager
    content_data = recipe_data.to_template_data()
    template_manager = TemplateManager()
    html = template_manager.render_report("COOKING", content_data)
    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
