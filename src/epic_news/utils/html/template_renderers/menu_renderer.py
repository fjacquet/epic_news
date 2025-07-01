"""
Menu Renderer

Renders menu planning data to structured HTML using BeautifulSoup.
Handles daily meal plans, ingredients, and nutritional information.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class MenuRenderer(BaseRenderer):
    """Renders menu planning content with structured formatting."""

    def render(self, data: dict[str, Any]) -> str:
        """
        Render menu planning data to HTML.

        Args:
            data: Dictionary containing menu planning data

        Returns:
            HTML string for menu planning content
        """
        # Create main container
        soup = self.create_soup("div", class_="menu-planner")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add weekly overview if available
        self._add_weekly_overview(soup, container, data)

        # Add daily meal plans
        self._add_daily_plans(soup, container, data)

        # Add shopping list if available
        self._add_shopping_list(soup, container, data)

        # Add nutritional information if available
        self._add_nutritional_info(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add menu planner header with title."""
        header = soup.new_tag("header", class_="menu-header")

        # Title
        title = data.get("title", "Menu Hebdomadaire")
        title_tag = soup.new_tag("h1", class_="menu-title")
        title_tag.string = f"🍽️ {title}"
        header.append(title_tag)

        # Date range if available
        date_range = data.get("date_range", "")
        if date_range:
            date_tag = soup.new_tag("p", class_="menu-date-range")
            date_tag.string = date_range
            header.append(date_tag)

        # Description if available
        description = data.get("description", "")
        if description:
            desc_tag = soup.new_tag("p", class_="menu-description")
            desc_tag.string = description
            header.append(desc_tag)

        container.append(header)

    def _add_weekly_overview(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add weekly menu overview if available."""
        overview = data.get("weekly_overview", "")
        if not overview:
            return

        overview_div = soup.new_tag("section", class_="menu-overview")

        overview_title = soup.new_tag("h2")
        overview_title.string = "📋 Aperçu de la semaine"
        overview_div.append(overview_title)

        overview_p = soup.new_tag("p")
        overview_p.string = overview
        overview_div.append(overview_p)

        container.append(overview_div)

    def _add_daily_plans(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add daily meal plans."""
        daily_plans = data.get("daily_plans", {})
        if not daily_plans:
            # Fallback to content if structured data not available
            content = data.get("content", "")
            if content:
                content_div = soup.new_tag("div", class_="menu-content")
                content_div.string = content
                container.append(content_div)
            return

        daily_plans_section = soup.new_tag("section", class_="daily-plans")

        plans_title = soup.new_tag("h2")
        plans_title.string = "🗓️ Menus Quotidiens"
        daily_plans_section.append(plans_title)

        # Iterate through each day's plan
        for day, meals in daily_plans.items():
            day_div = self._create_day_plan(soup, day, meals)
            daily_plans_section.append(day_div)

        container.append(daily_plans_section)

    def _create_day_plan(self, soup: BeautifulSoup, day: str, meals: dict[str, Any]) -> BeautifulSoup:
        """Create a daily meal plan card."""
        day_div = soup.new_tag("div", class_="day-plan")

        # Day header
        day_header = soup.new_tag("div", class_="day-header")

        # Add day emoji based on day name
        day_emoji = {
            "lundi": "1️⃣",
            "mardi": "2️⃣",
            "mercredi": "3️⃣",
            "jeudi": "4️⃣",
            "vendredi": "5️⃣",
            "samedi": "6️⃣",
            "dimanche": "7️⃣",
            "monday": "1️⃣",
            "tuesday": "2️⃣",
            "wednesday": "3️⃣",
            "thursday": "4️⃣",
            "friday": "5️⃣",
            "saturday": "6️⃣",
            "sunday": "7️⃣",
        }.get(day.lower(), "🗓️")

        day_title = soup.new_tag("h3")
        day_title.string = f"{day_emoji} {day}"
        day_header.append(day_title)

        day_div.append(day_header)

        # Meals container
        meals_div = soup.new_tag("div", class_="day-meals")

        # Standard meal types and their emojis
        meal_types = {
            "breakfast": "🍳 Petit-déjeuner",
            "lunch": "🥗 Déjeuner",
            "dinner": "🍲 Dîner",
            "snacks": "🍎 Collations",
            "petit-dejeuner": "🍳 Petit-déjeuner",
            "petit-déjeuner": "🍳 Petit-déjeuner",
            "dejeuner": "🥗 Déjeuner",
            "déjeuner": "🥗 Déjeuner",
            "diner": "🍲 Dîner",
            "dîner": "🍲 Dîner",
            "collations": "🍎 Collations",
        }

        if isinstance(meals, dict):
            # Create sections for each meal type
            for meal_type, meal_content in meals.items():
                meal_div = soup.new_tag("div", class_="meal")

                meal_name = meal_types.get(meal_type.lower(), f"🍽️ {meal_type}")
                meal_type_h4 = soup.new_tag("h4", class_="meal-type")
                meal_type_h4.string = meal_name
                meal_div.append(meal_type_h4)

                if isinstance(meal_content, list):
                    # Create list of dishes
                    dishes_list = soup.new_tag("ul", class_="dishes-list")
                    for dish in meal_content:
                        dish_item = soup.new_tag("li", class_="dish-item")
                        dish_item.string = dish
                        dishes_list.append(dish_item)
                    meal_div.append(dishes_list)
                else:
                    # Single dish or text description
                    meal_text = soup.new_tag("p", class_="meal-text")
                    meal_text.string = str(meal_content)
                    meal_div.append(meal_text)

                meals_div.append(meal_div)
        elif isinstance(meals, list):
            # Simple list of meals for the day
            dishes_list = soup.new_tag("ul", class_="dishes-list")
            for meal in meals:
                dish_item = soup.new_tag("li", class_="dish-item")
                dish_item.string = meal
                dishes_list.append(dish_item)
            meals_div.append(dishes_list)
        else:
            # Plain text content
            meal_text = soup.new_tag("p", class_="meal-text")
            meal_text.string = str(meals)
            meals_div.append(meal_text)

        day_div.append(meals_div)
        return day_div

    def _add_shopping_list(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add shopping list if available."""
        shopping_list = data.get("shopping_list", [])
        if not shopping_list:
            return

        shopping_section = soup.new_tag("section", class_="shopping-list")

        shopping_title = soup.new_tag("h2")
        shopping_title.string = "🛒 Liste de courses"
        shopping_section.append(shopping_title)

        # Group items by category if the data is structured that way
        if isinstance(shopping_list, dict):
            for category, items in shopping_list.items():
                category_div = soup.new_tag("div", class_="shopping-category")

                category_title = soup.new_tag("h3")
                category_title.string = category
                category_div.append(category_title)

                items_list = soup.new_tag("ul")
                for item in items:
                    item_li = soup.new_tag("li")
                    item_li.string = item
                    items_list.append(item_li)

                category_div.append(items_list)
                shopping_section.append(category_div)
        else:
            # Simple list of items
            items_list = soup.new_tag("ul")
            for item in shopping_list:
                item_li = soup.new_tag("li")
                item_li.string = item
                items_list.append(item_li)

            shopping_section.append(items_list)

        container.append(shopping_section)

    def _add_nutritional_info(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add nutritional information if available."""
        nutrition = data.get("nutritional_info", {})
        if not nutrition:
            return

        nutrition_section = soup.new_tag("section", class_="nutritional-info")

        nutrition_title = soup.new_tag("h2")
        nutrition_title.string = "🥗 Information Nutritionnelle"
        nutrition_section.append(nutrition_title)

        if isinstance(nutrition, dict):
            # Detailed nutritional information
            nutrition_table = soup.new_tag("table", class_="nutrition-table")

            # Table header
            thead = soup.new_tag("thead")
            tr = soup.new_tag("tr")

            th_nutrient = soup.new_tag("th")
            th_nutrient.string = "Nutriment"
            tr.append(th_nutrient)

            th_value = soup.new_tag("th")
            th_value.string = "Valeur"
            tr.append(th_value)

            thead.append(tr)
            nutrition_table.append(thead)

            # Table body
            tbody = soup.new_tag("tbody")
            for nutrient, value in nutrition.items():
                tr = soup.new_tag("tr")

                td_nutrient = soup.new_tag("td")
                td_nutrient.string = nutrient
                tr.append(td_nutrient)

                td_value = soup.new_tag("td")
                td_value.string = str(value)
                tr.append(td_value)

                tbody.append(tr)

            nutrition_table.append(tbody)
            nutrition_section.append(nutrition_table)
        else:
            # Simple text information
            nutrition_p = soup.new_tag("p")
            nutrition_p.string = str(nutrition)
            nutrition_section.append(nutrition_p)

        container.append(nutrition_section)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles to the menu planner."""
        style = soup.new_tag("style")
        style.string = """
        .menu-planner {
            max-width: 900px;
            margin: 0 auto;
            font-family: var(--body-font);
            color: var(--text-color);
        }
        .menu-header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--accent-color);
        }
        .menu-title {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
        }
        .menu-date-range {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .menu-description {
            font-style: italic;
            color: var(--text-muted);
        }
        .menu-overview, .shopping-list, .nutritional-info {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .menu-overview h2, .daily-plans h2, .shopping-list h2, .nutritional-info h2 {
            color: var(--heading-color);
            margin-top: 0;
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .daily-plans {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
            margin: 2rem 0;
        }
        @media (min-width: 768px) {
            .daily-plans {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        .day-plan {
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            overflow: hidden;
        }
        .day-header {
            background: var(--accent-color);
            color: white;
            padding: 0.75rem 1rem;
        }
        .day-header h3 {
            margin: 0;
            font-size: 1.2rem;
        }
        .day-meals {
            padding: 1.25rem;
        }
        .meal {
            margin-bottom: 1.5rem;
        }
        .meal:last-child {
            margin-bottom: 0;
        }
        .meal-type {
            color: var(--heading-color);
            margin: 0 0 0.75rem;
            font-size: 1.1rem;
        }
        .dishes-list {
            list-style-type: none;
            padding-left: 0.5rem;
            margin: 0.5rem 0;
        }
        .dish-item {
            position: relative;
            padding: 0.4rem 0.4rem 0.4rem 1.5rem;
            margin: 0.4rem 0;
        }
        .dish-item:before {
            content: "•";
            position: absolute;
            left: 0.4rem;
            color: var(--accent-color);
            font-weight: bold;
        }
        .shopping-category {
            margin-bottom: 1.5rem;
        }
        .shopping-category h3 {
            color: var(--heading-color);
            margin-bottom: 0.75rem;
            font-size: 1.1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.3rem;
        }
        .nutrition-table {
            width: 100%;
            border-collapse: collapse;
        }
        .nutrition-table th, .nutrition-table td {
            padding: 0.6rem;
            text-align: left;
            border: 1px solid var(--border-color);
        }
        .nutrition-table th {
            background: rgba(0,0,0,0.05);
        }
        .nutrition-table tr:nth-child(even) {
            background: rgba(0,0,0,0.02);
        }
        .menu-content {
            white-space: pre-wrap;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        """
        soup.append(style)
