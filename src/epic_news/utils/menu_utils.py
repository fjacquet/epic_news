"""Utilities for menu designer and cooking operations."""

import json
import logging
import os
from typing import Any

from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.utils.string_utils import create_topic_slug

logger = logging.getLogger(__name__)


def extract_html_from_json(json_report: str, html_output_path: str) -> bool:
    """
    Extract HTML content from a JSON file and save it as a standalone HTML file.
    Also embeds the CSS directly into the HTML file for better portability.

    Args:
        json_report: Path to the JSON file containing HTML content
        html_output_path: Path where the extracted HTML should be saved

    Returns:
        bool: True if extraction was successful, False otherwise
    """
    if not os.path.exists(json_report):
        logger.warning(f"⚠️ JSON report file not found: {json_report}")
        return False

    try:
        with open(json_report) as f:
            report_data = json.load(f)

        if "html_content" in report_data:
            html_content = report_data["html_content"]

            # Embed the CSS directly in the HTML for better portability
            html_content = embed_css_in_html(html_content)

            # Enhance the menu structure with improved formatting
            html_content = enhance_menu_structure(html_content)

            # Save the enhanced HTML content as a separate file
            with open(html_output_path, "w") as f:
                f.write(html_content)

            logger.info(f"✅ Enhanced HTML content saved to {html_output_path}")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to extract HTML content: {str(e)}")

    return False


def embed_css_in_html(html_content: str) -> str:
    """
    Embed the CSS directly in the HTML document for better portability.

    Args:
        html_content: The HTML content to modify

    Returns:
        str: HTML with embedded CSS
    """
    # Path to the CSS file relative to the project root
    css_path = os.path.join("templates", "css", "menu_report.css")

    # Check if the CSS file exists
    if not os.path.exists(css_path):
        logger.warning(f"⚠️ CSS file not found: {css_path}")
        return html_content

    try:
        # Read the CSS content
        with open(css_path) as f:
            css_content = f.read()

        # Replace the CSS link with embedded styles
        css_link = '<link rel="stylesheet" href="css/menu_report.css">'
        embedded_css = f"<style>\n{css_content}\n</style>"

        # Replace the link tag with embedded styles
        return html_content.replace(css_link, embedded_css)
    except Exception as e:
        logger.warning(f"⚠️ Failed to embed CSS: {str(e)}")
        return html_content


def enhance_menu_structure(html_content: str) -> str:
    """
    Enhance the menu structure with improved formatting and styling.

    Args:
        html_content: The HTML content to modify

    Returns:
        str: HTML with enhanced menu structure
    """
    # Add special class to daily meal sections for improved styling
    html_content = html_content.replace("<h3>Lundi:", '<h3 class="day-heading">Lundi:')
    html_content = html_content.replace("<h3>Mardi:", '<h3 class="day-heading">Mardi:')
    html_content = html_content.replace("<h3>Mercredi:", '<h3 class="day-heading">Mercredi:')
    html_content = html_content.replace("<h3>Jeudi:", '<h3 class="day-heading">Jeudi:')
    html_content = html_content.replace("<h3>Vendredi:", '<h3 class="day-heading">Vendredi:')
    html_content = html_content.replace("<h3>Samedi:", '<h3 class="day-heading">Samedi:')
    html_content = html_content.replace("<h3>Dimanche:", '<h3 class="day-heading">Dimanche:')

    # Enhance meal type formatting
    html_content = html_content.replace(
        "<strong>Petit-déjeuner", '<strong class="meal-type">🍳 Petit-déjeuner'
    )
    html_content = html_content.replace("<strong>Déjeuner", '<strong class="meal-type">🍲 Déjeuner')
    html_content = html_content.replace("<strong>Dîner", '<strong class="meal-type">🍽️ Dîner')

    # Add definition list styling for ingredients and nutritional info
    return html_content.replace("<ul>", '<ul class="feature-list">')


def process_recipes_from_menu(
    recipe_specs: list[dict[str, Any]], cooking_crew: CookingCrew = None
) -> list[str]:
    """
    Process a list of recipe specifications using the cooking crew.

    Args:
        recipe_specs: A list of recipe specifications from the menu structure
        cooking_crew: Optional cooking crew instance (will create one if not provided)

    Returns:
        List[str]: List of recipe slugs that were successfully processed
    """
    if cooking_crew is None:
        cooking_crew = CookingCrew().crew()

    total_recipes = len(recipe_specs)
    successful_recipes = []

    for i, recipe_spec in enumerate(recipe_specs):
        recipe_name = recipe_spec["name"]
        recipe_code = recipe_spec.get("code", "unspecified")
        # Generate slug directly from recipe name
        recipe_slug = create_topic_slug(recipe_name)
        logger.info(f"  - Recipe {i + 1}/{total_recipes}: {recipe_name} ({recipe_code})")

        try:
            # Direct CrewAI call with slug already included
            recipe_request = {
                "topic": recipe_spec["name"],
                "topic_slug": recipe_slug,  # Include slug directly
            }

            # Add preferences if available
            preferences = []
            if "type" in recipe_spec:
                preferences.append(f"Type: {recipe_spec['type']}")
            if "day" in recipe_spec:
                preferences.append(f"Day: {recipe_spec['day']}")
            if "meal" in recipe_spec:
                preferences.append(f"Meal: {recipe_spec['meal']}")

            # Only add preferences if we have any
            if preferences:
                recipe_request["preferences"] = ", ".join(preferences)

            cooking_crew.kickoff(inputs=recipe_request)
            successful_recipes.append(recipe_slug)

        except Exception as e:
            logger.error(f"  ❌ Error with {recipe_code}: {e}")

    return successful_recipes
