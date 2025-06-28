"""Template rendering utilities for HTML report generation."""

import os
from datetime import datetime
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


def render_menu_report(
    title: str,
    subtitle: str,
    menu_structure: str,
    generated_recipes: list[dict[str, Any]],
    recipe_files: list[str],
) -> str:
    """Render the menu report using the template."""

    # Format menu structure for HTML display instead of raw Python objects
    # If menu_structure contains Python object representations, format it properly
    if "DailyMenu(" in menu_structure or "DishInfo(" in menu_structure:
        # This is raw Python object string - we need to format it properly
        formatted_structure = "<p><em>Structure de menu générée automatiquement</em></p>"
        formatted_structure += (
            "<p>Le menu détaillé est disponible dans les fichiers de recettes individuels.</p>"
        )
    else:
        formatted_structure = menu_structure

    # Count different file types
    paprika_files = len([f for f in recipe_files if f.endswith(".yaml")])
    html_files = len([f for f in recipe_files if f.endswith(".html")])
    total_files = len(recipe_files)
    total_recipes = len(generated_recipes)

    # Calculate expected vs actual files
    expected_paprika = total_recipes
    expected_html = total_recipes
    expected_files = expected_paprika + expected_html
    completed_files = paprika_files + html_files
    progress_percentage = int(completed_files / expected_files * 100) if expected_files > 0 else 0

    # Prepare recipe data for template
    template_recipes = []
    for recipe_data in generated_recipes:
        recipe_info = {
            "name": recipe_data.get("name", "Recette"),
            "description": recipe_data.get("description", ""),
            "files": [],
        }

        # Add file links if available
        recipe_name = recipe_info["name"].lower().replace(" ", "-")
        for file_path in recipe_files:
            if recipe_name in file_path.lower():
                file_name = os.path.basename(file_path)
                recipe_info["files"].append({"name": file_name, "path": file_path})

        template_recipes.append(recipe_info)

    # Prepare template context
    context = {
        "title": title,
        "subtitle": subtitle,
        "menu_structure": formatted_structure,
        "generated_recipes": template_recipes,
        "total_recipes": total_recipes,
        "paprika_files": paprika_files,
        "html_files": html_files,
        "total_files": total_files,
        "expected_paprika": expected_paprika,
        "expected_html": expected_html,
        "expected_files": expected_files,
        "completed_files": completed_files,
        "progress_percentage": progress_percentage,
        "generation_date": datetime.now().strftime("%d/%m/%Y à %H:%M"),
    }
    return render_template("menu_report_template.html", context)


def render_universal_report(
    title: str,
    content: str,
    generation_date: str = None,
) -> str:
    """Render a universal report using the standard template.
    
    Args:
        title: Report title
        content: HTML content body
        generation_date: Optional generation date (defaults to current date)
    
    Returns:
        Rendered HTML string using universal template
    """
    if generation_date is None:
        generation_date = datetime.now().strftime("%d/%m/%Y à %H:%M")

    context = {
        "report_title": title,
        "report_body": content,
        "generation_date": generation_date,
    }

    return render_template("universal_report_template.html", context)


def render_shopping_list(
    title: str,
    generated_recipes: list[dict[str, Any]],
    total_recipes: int,
) -> str:
    """Render the shopping list using the template.

    Args:
        title: Shopping list title
        generated_recipes: List of generated recipe data
        total_recipes: Total number of recipes

    Returns:
        Rendered HTML shopping list
    """
    # Parse ingredients from actual generated recipes
    categories = _parse_ingredients_from_recipes(generated_recipes)

    # If no ingredients could be parsed, fall back to sample data
    if not categories:
        categories = _get_fallback_shopping_categories()

    context = {
        "title": title,
        "subtitle": f"Ingrédients pour {total_recipes} recettes de la semaine",
        "categories": categories,
        "total_recipes": total_recipes,
        "generation_date": datetime.now().strftime("%d/%m/%Y à %H:%M"),
    }

    return render_template("shopping_list_template.html", context)


def _parse_ingredients_from_recipes(generated_recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse ingredients from generated recipes and organize by category.

    Args:
        generated_recipes: List of recipe dictionaries

    Returns:
        List of ingredient categories with parsed ingredients
    """
    import re
    from collections import defaultdict

    # Ingredient categorization mapping
    ingredient_categories = {
        "Légumes et Fruits": {
            "emoji": "🥬🍅",
            "keywords": [
                "tomate",
                "courgette",
                "carotte",
                "oignon",
                "ail",
                "persil",
                "basilic",
                "salade",
                "concombre",
                "poivron",
                "aubergine",
                "haricot",
                "petit pois",
                "pomme",
                "citron",
                "orange",
                "herbe",
                "épinard",
                "brocoli",
                "chou",
            ],
        },
        "Viandes et Poissons": {
            "emoji": "🥩🐟",
            "keywords": [
                "poulet",
                "bœuf",
                "porc",
                "agneau",
                "veau",
                "saumon",
                "thon",
                "morue",
                "crevette",
                "poisson",
                "viande",
                "filet",
                "escalope",
                "côte",
                "rôti",
            ],
        },
        "Produits Laitiers": {
            "emoji": "🥛🧀",
            "keywords": [
                "lait",
                "crème",
                "beurre",
                "fromage",
                "yaourt",
                "œuf",
                "mascarpone",
                "parmesan",
                "gruyère",
                "mozzarella",
                "ricotta",
            ],
        },
        "Épicerie": {
            "emoji": "🍝🥖",
            "keywords": [
                "pâte",
                "riz",
                "farine",
                "pain",
                "huile",
                "vinaigre",
                "sel",
                "poivre",
                "sucre",
                "miel",
                "pâte",
                "céréale",
                "légumineuse",
                "haricot sec",
                "lentille",
            ],
        },
    }

    # Collect ingredients by category
    categorized_ingredients = defaultdict(set)

    for recipe in generated_recipes:
        # Try to extract ingredients from recipe result text
        recipe_text = str(recipe.get("result", ""))

        # Look for ingredient sections in the recipe text
        # Common patterns: "Ingrédients:", "- ", "• ", numbered lists
        ingredient_patterns = [
            r"(?:Ingrédients?|Ingredients?)[\s:]*\n(.*?)(?:\n\n|\nInstructions?|\nPréparation)",
            r"<ul[^>]*>(.*?)</ul>",
            r"<li[^>]*>(.*?)</li>",
        ]

        for pattern in ingredient_patterns:
            matches = re.findall(pattern, recipe_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Clean up HTML tags and extract ingredient names
                clean_text = re.sub(r"<[^>]+>", "", match)
                lines = clean_text.split("\n")

                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3:  # Skip very short lines
                        # Try to categorize this ingredient
                        categorized = False
                        for category_name, category_info in ingredient_categories.items():
                            for keyword in category_info["keywords"]:
                                if keyword.lower() in line.lower():
                                    # Extract quantity and ingredient name
                                    ingredient_info = _parse_ingredient_line(line)
                                    if ingredient_info:
                                        categorized_ingredients[category_name].add(
                                            (ingredient_info["name"], ingredient_info["quantity"])
                                        )
                                        categorized = True
                                        break
                            if categorized:
                                break

    # Convert to template format
    categories = []
    for category_name, category_info in ingredient_categories.items():
        if category_name in categorized_ingredients:
            ingredients = [
                {"name": name, "quantity": quantity}
                for name, quantity in sorted(categorized_ingredients[category_name])
            ]
            if ingredients:  # Only add categories that have ingredients
                categories.append(
                    {"name": category_name, "emoji": category_info["emoji"], "ingredients": ingredients}
                )

    return categories


def _parse_ingredient_line(line: str) -> dict[str, str] | None:
    """Parse a single ingredient line to extract name and quantity.

    Args:
        line: Raw ingredient line text

    Returns:
        Dictionary with 'name' and 'quantity' keys, or None if parsing fails
    """
    import re

    # Clean up the line
    line = line.strip().lstrip("•-*").strip()

    # Common quantity patterns
    quantity_patterns = [
        r"^(\d+(?:[.,]\d+)?\s*(?:kg|g|l|ml|cl|cuillères?|c\.|cs|cc|pièces?|tranches?))\s+(.+)",
        r"^(\d+(?:[.,]\d+)?)\s+(.+)",
        r"^(.+?)\s*[:-]\s*(\d+(?:[.,]\d+)?\s*(?:kg|g|l|ml|cl|cuillères?|c\.|cs|cc|pièces?|tranches?))",
    ]

    for pattern in quantity_patterns:
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            if "kg|g|l|ml" in pattern:  # First pattern - quantity first
                return {"quantity": match.group(1), "name": match.group(2).strip()}
            # Other patterns
            return {"name": match.group(2).strip(), "quantity": match.group(1).strip()}

    # If no quantity pattern matches, treat whole line as ingredient name
    if len(line) > 2:
        return {"name": line, "quantity": "selon besoin"}

    return None


def _get_fallback_shopping_categories() -> list[dict[str, Any]]:
    """Get fallback shopping categories when ingredient parsing fails."""
    return [
        {
            "name": "Légumes et Fruits",
            "emoji": "🥬🍅",
            "ingredients": [
                {"name": "Tomates", "quantity": "2 kg"},
                {"name": "Courgettes", "quantity": "1.5 kg"},
                {"name": "Haricots verts", "quantity": "800g"},
                {"name": "Salade verte", "quantity": "3 pièces"},
            ],
        },
        {
            "name": "Viandes et Poissons",
            "emoji": "🥩🐟",
            "ingredients": [
                {"name": "Poulet", "quantity": "1.5 kg"},
                {"name": "Bœuf", "quantity": "800g"},
                {"name": "Poisson blanc", "quantity": "600g"},
            ],
        },
        {
            "name": "Produits Laitiers",
            "emoji": "🥛🧀",
            "ingredients": [
                {"name": "Lait", "quantity": "2L"},
                {"name": "Fromage râpé", "quantity": "200g"},
                {"name": "Beurre", "quantity": "250g"},
            ],
        },
        {
            "name": "Épicerie",
            "emoji": "🍝🥖",
            "ingredients": [
                {"name": "Pâtes", "quantity": "500g"},
                {"name": "Riz", "quantity": "1kg"},
                {"name": "Pain", "quantity": "selon besoin quotidien"},
            ],
        },
    ]
