"""Template rendering utilities for HTML report generation.

Only generic Jinja2 helpers remain. Menu/shopping helpers have been removed
in favor of TemplateManager and specialized renderers via RendererFactory.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_template_environment() -> Environment:
    """Create and configure Jinja2 environment for template rendering."""
    # Get the project root directory (go up from src/epic_news/utils/html/templates.py to project root)
    project_root = Path(__file__).parent.parent.parent.parent.parent
    templates_dir = project_root / "templates"

    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filters
    env.filters["datetime_format"] = lambda dt, fmt="%d/%m/%Y à %H:%M": dt.strftime(fmt)

    return env


def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a template with the given context.

    Args:
        template_name: Name of the template file (e.g., 'menu_report_template.html')
        context: Dictionary of variables to pass to the template

    Returns:
        Rendered HTML string
    """
    env = get_template_environment()
    template = env.get_template(template_name)
    return template.render(**context)


# NOTE: render_menu_report has been removed.
# Use TemplateManager.render_report(selected_crew="MENU", content_data=...) instead.
# NOTE: render_shopping_list has been removed. Use ShoppingRenderer via TemplateManager.
