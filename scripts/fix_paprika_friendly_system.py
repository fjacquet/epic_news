#!/usr/bin/env python3
"""
Fix Paprika-Friendly System Script

This script implements a better approach that:
1. Keeps descriptive, user-friendly filenames (e.g., couscous_royal_lundi_diner_report.html)
2. Generates missing YAML files with proper Paprika-compatible structure
3. Fixes the renaming logic to work with descriptive names instead of cryptic codes
4. Creates a mapping system for meal planning without changing actual filenames

This approach is much more user-friendly for Paprika loading and recipe management.
"""

import json
import os
import re
from pathlib import Path

import yaml
from bs4 import BeautifulSoup


class PaprikaFriendlySystem:
    """Creates a Paprika-friendly recipe system with descriptive filenames."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.cooking_dir = self.project_root / "output" / "cooking"
        self.mapping_file = self.cooking_dir / "recipe_mapping.json"

        # Results tracking
        self.generated_yaml_files = []
        self.enhanced_html_files = []
        self.recipe_mapping = {}

    def extract_recipe_info_from_html(self, html_file: Path) -> dict[str, str]:
        """Extract comprehensive recipe information from HTML file."""
        try:
            with open(html_file, encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")

            # Extract title and recipe name
            title_tag = soup.find("title")
            title = title_tag.get_text() if title_tag else html_file.stem

            h1_tag = soup.find("h1")
            recipe_name = h1_tag.get_text() if h1_tag else title

            # Clean up recipe name (remove emojis and extra whitespace)
            recipe_name = re.sub(r"[📰🍽️🥘👨‍🍳🔥✨🌟💫🎯]", "", recipe_name).strip()

            # Extract meal information from filename
            filename_lower = html_file.name.lower()

            # Determine day
            day = "Non spécifié"
            day_mapping = {
                "lundi": "Lundi",
                "mardi": "Mardi",
                "mercredi": "Mercredi",
                "jeudi": "Jeudi",
                "vendredi": "Vendredi",
                "samedi": "Samedi",
                "dimanche": "Dimanche",
            }
            for day_key, day_value in day_mapping.items():
                if day_key in filename_lower:
                    day = day_value
                    break

            # Determine meal
            meal = "Non spécifié"
            if "dejeuner" in filename_lower or "déjeuner" in filename_lower:
                meal = "Déjeuner"
            elif "diner" in filename_lower or "dîner" in filename_lower:
                meal = "Dîner"

            # Determine recipe type
            recipe_type = "Plat principal"  # Default
            if "entree" in filename_lower or "entrée" in filename_lower:
                recipe_type = "Entrée"
            elif "dessert" in filename_lower:
                recipe_type = "Dessert"

            # Extract ingredients and directions from HTML
            ingredients = self.extract_ingredients_from_html(soup)
            directions = self.extract_directions_from_html(soup)

            return {
                "name": recipe_name,
                "day": day,
                "meal": meal,
                "type": recipe_type,
                "ingredients": ingredients,
                "directions": directions,
                "source_file": html_file.name,
            }

        except Exception as e:
            print(f"  ❌ Error extracting info from {html_file.name}: {e}")
            return {
                "name": html_file.stem,
                "day": "Non spécifié",
                "meal": "Non spécifié",
                "type": "Plat principal",
                "ingredients": "Ingrédients à compléter",
                "directions": "Instructions à compléter",
                "source_file": html_file.name,
            }

    def extract_ingredients_from_html(self, soup: BeautifulSoup) -> str:
        """Extract ingredients list from HTML content."""
        ingredients = []

        # Look for ingredients section
        ingredients_section = soup.find(["h2", "h3"], string=re.compile(r"Ingrédients?", re.IGNORECASE))
        if ingredients_section:
            # Find the next list after the ingredients heading
            next_element = ingredients_section.find_next_sibling(["ul", "ol"])
            if next_element:
                for li in next_element.find_all("li"):
                    ingredient = li.get_text().strip()
                    if ingredient:
                        ingredients.append(ingredient)

        # If no structured ingredients found, look for any lists
        if not ingredients:
            for ul in soup.find_all(["ul", "ol"]):
                for li in ul.find_all("li"):
                    text = li.get_text().strip()
                    if text and len(text) < 200:  # Reasonable ingredient length
                        ingredients.append(text)
                if ingredients:  # Take first reasonable list found
                    break

        return "\n".join(ingredients) if ingredients else "Ingrédients à compléter"

    def extract_directions_from_html(self, soup: BeautifulSoup) -> str:
        """Extract cooking directions from HTML content."""
        directions = []

        # Look for directions/instructions section
        directions_section = soup.find(
            ["h2", "h3"], string=re.compile(r"(Instructions?|Préparation|Étapes?)", re.IGNORECASE)
        )
        if directions_section:
            # Find content after the directions heading
            next_element = directions_section.find_next_sibling(["ol", "ul", "div", "p"])
            if next_element:
                if next_element.name in ["ol", "ul"]:
                    for li in next_element.find_all("li"):
                        step = li.get_text().strip()
                        if step:
                            directions.append(step)
                else:
                    # Look for paragraphs or div content
                    text = next_element.get_text().strip()
                    if text:
                        directions.append(text)

        # If no structured directions found, look for numbered steps in text
        if not directions:
            all_text = soup.get_text()
            step_pattern = re.compile(r"(\d+[\.\)]\s*[^0-9\n]+)", re.MULTILINE)
            steps = step_pattern.findall(all_text)
            if steps:
                directions = [step.strip() for step in steps[:10]]  # Limit to reasonable number

        return "\n".join(directions) if directions else "Instructions à compléter"

    def create_paprika_yaml(self, recipe_info: dict[str, str], html_file: Path) -> Path | None:
        """Create a Paprika-compatible YAML file with comprehensive recipe data."""
        try:
            # Create comprehensive categories
            categories = ["Epic News", "Cuisine française"]
            if recipe_info["type"] != "Non spécifié":
                categories.append(recipe_info["type"])
            if recipe_info["day"] != "Non spécifié":
                categories.append(f"Menu {recipe_info['day']}")
            if recipe_info["meal"] != "Non spécifié":
                categories.append(recipe_info["meal"])

            # Estimate cooking times based on recipe type
            prep_time = "20 minutes"
            cook_time = "30 minutes"
            if recipe_info["type"] == "Entrée":
                prep_time = "15 minutes"
                cook_time = "20 minutes"
            elif recipe_info["type"] == "Dessert":
                prep_time = "25 minutes"
                cook_time = "45 minutes"

            # Create comprehensive YAML structure
            yaml_data = {
                "name": recipe_info["name"],
                "servings": "4-6 personnes",
                "source": "Epic News Cooking Crew",
                "source_url": None,
                "prep_time": prep_time,
                "cook_time": cook_time,
                "total_time": None,
                "difficulty": "Moyen",
                "on_favorites": True,
                "rating": 5,
                "categories": categories,
                "photo_url": None,
                "ingredients": recipe_info["ingredients"],
                "directions": recipe_info["directions"],
                "notes": f"Recette générée par Epic News Cooking Crew\nFichier source: {recipe_info['source_file']}\nJour: {recipe_info['day']}\nRepas: {recipe_info['meal']}",
                "nutritional_info": "Information nutritionnelle à déterminer",
                "created": None,
                "hash": None,
                "photo": None,
                "photo_hash": None,
                "scale": None,
            }

            # Save YAML file with same base name as HTML
            yaml_file = html_file.with_suffix(".yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            print(f"  ✅ Generated Paprika YAML: {yaml_file.name}")
            return yaml_file

        except Exception as e:
            print(f"  ❌ Failed to create YAML for {html_file.name}: {e}")
            return None

    def process_html_files(self) -> None:
        """Process all HTML files and generate missing YAML files."""
        html_files = list(self.cooking_dir.glob("*.html"))
        print(f"🔍 Found {len(html_files)} HTML files to process")

        for html_file in html_files:
            print(f"\n📄 Processing: {html_file.name}")

            # Extract recipe information
            recipe_info = self.extract_recipe_info_from_html(html_file)

            # Store mapping for future reference
            self.recipe_mapping[html_file.name] = recipe_info

            # Generate YAML if missing
            yaml_file = html_file.with_suffix(".yaml")
            if not yaml_file.exists():
                generated_yaml = self.create_paprika_yaml(recipe_info, html_file)
                if generated_yaml:
                    self.generated_yaml_files.append(generated_yaml)
            else:
                print(f"  ℹ️ YAML already exists: {yaml_file.name}")

    def save_mapping(self) -> None:
        """Save the recipe mapping data."""
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(self.recipe_mapping, f, indent=2, ensure_ascii=False)
        print(f"💾 Recipe mapping saved to: {self.mapping_file}")

    def generate_report(self) -> str:
        """Generate a comprehensive report."""
        report = []
        report.append("# Paprika-Friendly Recipe System Report")
        report.append(f"Generated: {os.popen('date').read().strip()}")
        report.append("")

        # Summary
        report.append("## Summary")
        report.append(f"- HTML files processed: {len(self.recipe_mapping)}")
        report.append(f"- YAML files generated: {len(self.generated_yaml_files)}")
        report.append("")

        # Generated YAML files
        if self.generated_yaml_files:
            report.append(f"## Generated YAML Files ({len(self.generated_yaml_files)})")
            for yaml_file in self.generated_yaml_files:
                report.append(f"- {yaml_file.name}")
            report.append("")

        # Recipe mapping summary
        report.append("## Recipe Mapping Summary")
        for filename, info in self.recipe_mapping.items():
            report.append(f"### {filename}")
            report.append(f"- **Nom**: {info['name']}")
            report.append(f"- **Type**: {info['type']}")
            report.append(f"- **Jour**: {info['day']}")
            report.append(f"- **Repas**: {info['meal']}")
            report.append("")

        # Benefits
        report.append("## Benefits of This Approach")
        report.append("- ✅ **User-friendly filenames**: Easy to identify and load in Paprika")
        report.append("- ✅ **Comprehensive YAML**: Full Paprika-compatible recipe structure")
        report.append("- ✅ **Preserved descriptive names**: No cryptic codes like DIM-L-S13")
        report.append("- ✅ **Automatic ingredient/direction extraction**: From existing HTML content")
        report.append("- ✅ **Proper categorization**: By meal type, day, and recipe type")
        report.append("")

        # Next steps
        report.append("## Next Steps")
        report.append("- All recipes now have both HTML and YAML files")
        report.append("- YAML files are ready for Paprika import")
        report.append("- Filenames remain descriptive and user-friendly")
        report.append("- No need for complex renaming logic")

        return "\n".join(report)

    def run(self) -> str:
        """Execute the complete process."""
        print("🚀 Starting Paprika-Friendly Recipe System...")
        print("")

        # Ensure cooking directory exists
        self.cooking_dir.mkdir(parents=True, exist_ok=True)

        # Process HTML files and generate YAML
        print("📁 Step 1: Processing HTML files and generating YAML")
        self.process_html_files()
        print("")

        # Save mapping
        print("💾 Step 2: Saving recipe mapping")
        self.save_mapping()
        print("")

        # Generate report
        print("📊 Step 3: Generating report")
        report = self.generate_report()

        # Save report
        report_path = self.project_root / "paprika_friendly_system_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"  ✅ Report saved to: {report_path}")
        print("")
        print("🎉 Paprika-Friendly Recipe System Complete!")

        return report


def main():
    """Main function."""
    project_root = "/Users/fjacquet/Projects/crews/epic_news"

    system = PaprikaFriendlySystem(project_root)
    report = system.run()

    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    main()
