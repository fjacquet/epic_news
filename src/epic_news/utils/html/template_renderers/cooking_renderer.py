"""
Cooking Renderer

Renders cooking recipe data to structured HTML using BeautifulSoup.
Handles recipe details, ingredients, instructions and metadata.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class CookingRenderer(BaseRenderer):
    """Renders cooking recipe content with structured formatting."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()

    def render(self, data: dict[str, Any]) -> str:
        """
        Render cooking recipe data to HTML.

        Args:
            data: Dictionary containing recipe data

        Returns:
            HTML string for recipe content
        """
        # Create main container
        soup = self.create_soup("div", class_="recipe-container")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add recipe metadata
        self._add_metadata(soup, container, data)

        # Add ingredients section
        self._add_ingredients(soup, container, data)

        # Add instructions section
        self._add_instructions(soup, container, data)

        # Add chef notes if available
        self._add_chef_notes(soup, container, data)

        # Add nutritional info if available
        self._add_nutritional_info(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add recipe header with title and description."""
        header = soup.new_tag("header", class_="recipe-header")

        # Title
        title = data.get("recipe_title", data.get("name", "Recette"))
        title_tag = soup.new_tag("h1", class_="recipe-title")
        title_tag.string = f"🍽️ {title}"
        header.append(title_tag)

        # Description
        description = data.get("description", "")
        if description:
            desc_tag = soup.new_tag("p", class_="recipe-description")
            desc_tag.string = description
            header.append(desc_tag)

        # Add recipe type badge if available
        recipe_type = data.get("type", data.get("category", ""))
        if recipe_type:
            badge = soup.new_tag("span", class_="recipe-badge")
            badge.string = recipe_type
            header.append(badge)

        container.append(header)

    def _add_metadata(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add recipe metadata (prep time, cook time, servings, etc.)."""
        meta_div = soup.new_tag("div", class_="recipe-meta")

        # Add preparation time if available
        prep_time = data.get("prep_time", "")
        if prep_time:
            prep_div = soup.new_tag("div", class_="meta-item")
            prep_strong = soup.new_tag("strong")
            prep_strong.string = "⏱️ Préparation: "
            prep_div.append(prep_strong)
            prep_div.append(soup.new_string(prep_time))
            meta_div.append(prep_div)

        # Add cooking time if available
        cook_time = data.get("cook_time", "")
        if cook_time:
            cook_div = soup.new_tag("div", class_="meta-item")
            cook_strong = soup.new_tag("strong")
            cook_strong.string = "🔥 Cuisson: "
            cook_div.append(cook_strong)
            cook_div.append(soup.new_string(cook_time))
            meta_div.append(cook_div)

        # Add servings if available
        servings = data.get("servings", "")
        if servings:
            serv_div = soup.new_tag("div", class_="meta-item")
            serv_strong = soup.new_tag("strong")
            serv_strong.string = "👥 Portions: "
            serv_div.append(serv_strong)
            serv_div.append(soup.new_string(str(servings)))
            meta_div.append(serv_div)

        # Add difficulty if available
        difficulty = data.get("difficulty", "")
        if difficulty:
            # Map difficulty to emoji
            difficulty_emoji = {
                "facile": "🟢 Facile",
                "moyen": "🟡 Moyen",
                "difficile": "🔴 Difficile",
                "easy": "🟢 Facile",
                "medium": "🟡 Moyen",
                "hard": "🔴 Difficile",
            }.get(difficulty.lower(), difficulty)

            diff_div = soup.new_tag("div", class_="meta-item")
            diff_strong = soup.new_tag("strong")
            diff_strong.string = "📊 Difficulté: "
            diff_div.append(diff_strong)
            diff_div.append(soup.new_string(difficulty_emoji))
            meta_div.append(diff_div)

        # Add category if available
        category = data.get("category", "")
        if category:
            cat_div = soup.new_tag("div", class_="meta-item")
            cat_strong = soup.new_tag("strong")
            cat_strong.string = "🏷️ Catégorie: "
            cat_div.append(cat_strong)
            cat_div.append(soup.new_string(category))
            meta_div.append(cat_div)

        if len(meta_div.contents) > 0:
            container.append(meta_div)

    def _add_ingredients(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add ingredients section with structured list."""
        ingredients = data.get("ingredients", [])
        if not ingredients:
            return

        ingredients_section = soup.new_tag("section", class_="recipe-ingredients")

        # Add section title
        ing_title = soup.new_tag("h2")
        ing_title.string = "🧂 Ingrédients"
        ingredients_section.append(ing_title)

        # Create ingredients list
        ing_list = soup.new_tag("ul", class_="ingredients-list")
        for ingredient in ingredients:
            ing_item = soup.new_tag("li")
            ing_item.string = f"🥄 {ingredient}"
            ing_list.append(ing_item)

        ingredients_section.append(ing_list)
        container.append(ingredients_section)

    def _add_instructions(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add instructions section with numbered steps."""
        instructions = data.get("instructions", [])
        if not instructions:
            return

        instructions_section = soup.new_tag("section", class_="recipe-instructions")

        # Add section title
        ins_title = soup.new_tag("h2")
        ins_title.string = "📝 Instructions"
        instructions_section.append(ins_title)

        # Create instructions list
        ins_list = soup.new_tag("ol", class_="instructions-list")
        for instruction in instructions:
            ins_item = soup.new_tag("li")
            ins_item.string = instruction
            ins_list.append(ins_item)

        instructions_section.append(ins_list)
        container.append(instructions_section)

    def _add_chef_notes(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add chef notes if available."""
        chef_notes = data.get("chef_notes", "")
        if not chef_notes:
            return

        notes_section = soup.new_tag("section", class_="chef-notes")

        notes_title = soup.new_tag("h3")
        notes_title.string = "👨‍🍳 Notes du Chef"
        notes_section.append(notes_title)

        # Handle both string and list inputs
        if isinstance(chef_notes, list):
            notes_list = soup.new_tag("ul", class_="notes-list")
            for note in chef_notes:
                note_item = soup.new_tag("li")
                note_item.string = str(note)
                notes_list.append(note_item)
            notes_section.append(notes_list)
        else:
            notes_content = soup.new_tag("p")
            notes_content.string = str(chef_notes)
            notes_section.append(notes_content)

        container.append(notes_section)

    def _add_nutritional_info(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add nutritional information if available."""
        nutritional_info = data.get("nutritional_info", "")
        if not nutritional_info:
            return

        nutrition_section = soup.new_tag("section", class_="nutritional-info")

        nutrition_title = soup.new_tag("h3")
        nutrition_title.string = "🥗 Information Nutritionnelle"
        nutrition_section.append(nutrition_title)

        # Handle both string and dictionary inputs
        if isinstance(nutritional_info, dict):
            nutrition_list = soup.new_tag("ul", class_="nutrition-list")
            for key, value in nutritional_info.items():
                nutrition_item = soup.new_tag("li")
                nutrition_item.string = f"{key.replace('_', ' ').title()}: {value}"
                nutrition_list.append(nutrition_item)
            nutrition_section.append(nutrition_list)
        else:
            nutrition_content = soup.new_tag("p")
            nutrition_content.string = str(nutritional_info)
            nutrition_section.append(nutrition_content)

        container.append(nutrition_section)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles to the recipe."""
        style = soup.new_tag("style")
        style.string = """
        .recipe-container {
            max-width: 800px;
            margin: 0 auto;
            font-family: var(--body-font);
            color: var(--text-color);
        }
        .recipe-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--highlight-bg);
            border-radius: 8px;
            border-left: 4px solid var(--heading-color);
            box-shadow: 0 2px 4px var(--shadow-color);
            transition: all 0.3s;
        }
        .recipe-title {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
            font-size: 2.2em;
            font-weight: 600;
        }
        .recipe-description {
            font-style: italic;
            color: var(--text-color);
            font-size: 1.1em;
            opacity: 0.9;
            margin-bottom: 1rem;
        }
        .recipe-badge {
            display: inline-block;
            background: var(--heading-color);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
            margin-top: 1rem;
        }
        .recipe-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            box-shadow: 0 2px 4px var(--shadow-color);
            transition: all 0.3s;
        }
        .meta-item {
            background: var(--highlight-bg);
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
            border-left: 3px solid var(--heading-color);
            transition: all 0.3s;
        }
        .meta-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .recipe-ingredients, .recipe-instructions, .chef-notes, .nutritional-info {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            box-shadow: 0 2px 4px var(--shadow-color);
            transition: all 0.3s;
        }
        .recipe-ingredients:hover, .recipe-instructions:hover, .chef-notes:hover, .nutritional-info:hover {
            box-shadow: 0 4px 8px var(--shadow-color);
        }
        .recipe-ingredients h2, .recipe-instructions h2, .chef-notes h3, .nutritional-info h3 {
            color: var(--heading-color);
            margin-top: 0;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
        }
        .ingredients-list {
            list-style-type: none;
            padding-left: 0;
        }
        .ingredients-list li {
            margin: 0.8rem 0;
            padding: 1rem;
            background: var(--highlight-bg);
            border-radius: 6px;
            border-left: 4px solid #28a745;
            transition: all 0.3s;
            display: flex;
            align-items: center;
        }
        .ingredients-list li:hover {
            background: var(--border-color);
            transform: translateX(4px);
        }
        .instructions-list {
            padding-left: 0;
            counter-reset: step-counter;
        }
        .instructions-list li {
            margin: 1.2rem 0;
            padding: 1.2rem;
            background: var(--highlight-bg);
            border-radius: 6px;
            border-left: 4px solid #007bff;
            position: relative;
            counter-increment: step-counter;
            transition: all 0.3s;
        }
        .instructions-list li:hover {
            background: var(--border-color);
            transform: translateX(4px);
        }
        .instructions-list li::before {
            content: counter(step-counter);
            position: absolute;
            left: -15px;
            top: 50%;
            transform: translateY(-50%);
            background: #007bff;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }
        .chef-notes, .nutritional-info {
            border-left: 4px solid #ffc107;
        }
        .chef-notes h3, .nutritional-info h3 {
            color: var(--h3-color);
        }
        .notes-list {
            list-style-type: none;
            padding-left: 0;
        }
        .notes-list li {
            margin: 0.8rem 0;
            padding: 1rem;
            background: var(--highlight-bg);
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            transition: all 0.3s;
            position: relative;
        }
        .notes-list li:hover {
            background: var(--border-color);
            transform: translateX(4px);
        }
        .notes-list li::before {
            content: "💡";
            position: absolute;
            left: -15px;
            top: 50%;
            transform: translateY(-50%);
            background: #ffc107;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
        }
        .nutrition-list {
            list-style-type: none;
            padding-left: 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 0.8rem;
        }
        .nutrition-list li {
            margin: 0;
            padding: 1rem;
            background: var(--highlight-bg);
            border-radius: 6px;
            border-left: 4px solid #28a745;
            transition: all 0.3s;
            text-align: center;
            font-weight: 500;
        }
        .nutrition-list li:hover {
            background: var(--border-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        """
        soup.append(style)
