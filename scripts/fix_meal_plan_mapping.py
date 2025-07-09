#!/usr/bin/env python3
"""
Fix Meal Plan Mapping Script

This script addresses the disconnect between two file naming systems:
1. Menu Designer System: LUN-D-M01.html (time-based codes)
2. Individual Recipe System: couscous_royal_lundi_diner_report.html (descriptive names)

The script will:
- Create a mapping between descriptive filenames and meal plan codes
- Generate missing YAML files for all existing HTML files
- Create symbolic links or copies with time-based codes for the renaming system
- Fix the meal plan structure to work with both systems
"""

import json
import os
import re
from pathlib import Path

import yaml


class MealPlanMapper:
    """Maps descriptive recipe filenames to meal plan codes and generates missing files."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.cooking_dir = self.project_root / "output" / "cooking"
        self.mapping_file = self.cooking_dir / "meal_plan_mapping.json"

        # Meal plan code structure
        self.day_codes = {
            "lundi": "LUN",
            "mardi": "MAR",
            "mercredi": "MER",
            "jeudi": "JEU",
            "vendredi": "VEN",
            "samedi": "SAM",
            "dimanche": "DIM",
        }
        self.meal_codes = {"dejeuner": "L", "diner": "D", "déjeuner": "L", "dîner": "D"}
        self.type_codes = {"entree": "S", "entrée": "S", "plat": "M", "dessert": "D"}

        # Counters for generating unique codes
        self.counters = {"S": 1, "M": 1, "D": 1}

        # Results tracking
        self.mapped_files = []
        self.generated_yaml_files = []
        self.created_time_based_files = []
        self.mapping_data = {}

    def extract_meal_info_from_filename(self, filename: str) -> dict[str, str] | None:
        """Extract day, meal, and type information from descriptive filename."""
        filename_lower = filename.lower()

        # Extract day
        day = None
        for day_name, _code in self.day_codes.items():
            if day_name in filename_lower:
                day = day_name
                break

        # Extract meal
        meal = None
        for meal_name, _code in self.meal_codes.items():
            if meal_name in filename_lower:
                meal = meal_name
                break

        # Extract type (entrée, plat principal, dessert)
        recipe_type = None
        if "entree" in filename_lower or "entrée" in filename_lower:
            recipe_type = "entrée"
        elif "plat" in filename_lower:
            recipe_type = "plat"
        elif "dessert" in filename_lower:
            recipe_type = "dessert"
        else:
            # Default to main course if not specified
            recipe_type = "plat"

        if day and meal:
            return {
                "day": day,
                "meal": meal,
                "type": recipe_type,
                "day_code": self.day_codes[day],
                "meal_code": self.meal_codes[meal],
                "type_code": self.type_codes[recipe_type],
            }

        return None

    def generate_time_based_code(self, meal_info: dict[str, str]) -> str:
        """Generate a time-based code like LUN-D-M01."""
        type_code = meal_info["type_code"]
        counter = self.counters[type_code]
        self.counters[type_code] += 1

        return f"{meal_info['day_code']}-{meal_info['meal_code']}-{type_code}{counter:02d}"

    def create_yaml_from_html(self, html_file: Path) -> Path | None:
        """Create a YAML file from an HTML file by extracting recipe information."""
        try:
            with open(html_file, encoding="utf-8") as f:
                html_content = f.read()

            # Extract title from HTML
            title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
            title = title_match.group(1) if title_match else html_file.stem

            # Extract recipe name from h1 tag
            h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL)
            recipe_name = h1_match.group(1) if h1_match else title

            # Clean up recipe name (remove emojis and HTML tags)
            recipe_name = re.sub(r"<[^>]+>", "", recipe_name)
            recipe_name = re.sub(r"[📰🍽️🥘👨‍🍳]", "", recipe_name).strip()

            # Extract meal info for categories
            meal_info = self.extract_meal_info_from_filename(html_file.name)
            categories = ["Cuisine française", "Thermomix"]
            if meal_info:
                categories.extend(
                    [meal_info["type"].title(), meal_info["day"].title(), meal_info["meal"].title()]
                )

            # Create YAML structure compatible with Paprika
            yaml_data = {
                "name": recipe_name,
                "servings": "4-6",
                "source": "Epic News Cooking Crew",
                "source_url": None,
                "prep_time": "20 minutes",
                "cook_time": "30 minutes",
                "on_favorites": True,
                "categories": categories,
                "nutritional_info": "Information nutritionnelle à déterminer",
                "difficulty": "Moyen",
                "rating": 5,
                "notes": f"Recette générée automatiquement à partir de {html_file.name}",
                "ingredients": "Ingrédients à extraire du contenu HTML",
                "directions": "Instructions à extraire du contenu HTML",
            }

            # Save YAML file
            yaml_file = html_file.with_suffix(".yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            print(f"  ✅ Generated YAML: {yaml_file.name}")
            return yaml_file

        except Exception as e:
            print(f"  ❌ Failed to create YAML for {html_file.name}: {e}")
            return None

    def create_time_based_links(self, original_file: Path, time_based_code: str) -> list[Path]:
        """Create time-based filename links for both HTML and YAML files."""
        created_files = []

        for extension in [".html", ".yaml"]:
            original_with_ext = original_file.with_suffix(extension)
            if original_with_ext.exists():
                time_based_file = self.cooking_dir / f"{time_based_code}{extension}"

                try:
                    # Create a copy (not symlink) to avoid issues with the renaming system
                    import shutil

                    shutil.copy2(original_with_ext, time_based_file)
                    created_files.append(time_based_file)
                    print(f"  ✅ Created time-based file: {time_based_file.name}")
                except Exception as e:
                    print(f"  ❌ Failed to create {time_based_file.name}: {e}")

        return created_files

    def process_html_files(self) -> None:
        """Process all HTML files in the cooking directory."""
        html_files = list(self.cooking_dir.glob("*.html"))
        print(f"🔍 Found {len(html_files)} HTML files to process")

        for html_file in html_files:
            print(f"\n📄 Processing: {html_file.name}")

            # Extract meal information
            meal_info = self.extract_meal_info_from_filename(html_file.name)
            if not meal_info:
                print(f"  ⚠️ Could not extract meal info from {html_file.name}")
                continue

            # Generate time-based code
            time_based_code = self.generate_time_based_code(meal_info)

            # Store mapping
            self.mapping_data[html_file.name] = {
                "time_based_code": time_based_code,
                "meal_info": meal_info,
                "original_path": str(html_file),
            }

            # Generate YAML if missing
            yaml_file = html_file.with_suffix(".yaml")
            if not yaml_file.exists():
                generated_yaml = self.create_yaml_from_html(html_file)
                if generated_yaml:
                    self.generated_yaml_files.append(generated_yaml)

            # Create time-based filename copies
            time_based_files = self.create_time_based_links(html_file, time_based_code)
            self.created_time_based_files.extend(time_based_files)

            self.mapped_files.append(
                {"original": html_file.name, "time_based_code": time_based_code, "meal_info": meal_info}
            )

    def save_mapping(self) -> None:
        """Save the mapping data to a JSON file."""
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(self.mapping_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Mapping saved to: {self.mapping_file}")

    def generate_report(self) -> str:
        """Generate a comprehensive report of the mapping process."""
        report = []
        report.append("# Meal Plan Mapping Report")
        report.append(f"Generated: {os.popen('date').read().strip()}")
        report.append("")

        # Mapping summary
        report.append(f"## File Mapping Summary: {len(self.mapped_files)}")
        for mapping in self.mapped_files:
            report.append(f"- {mapping['original']} → {mapping['time_based_code']}")
            report.append(f"  - Day: {mapping['meal_info']['day'].title()}")
            report.append(f"  - Meal: {mapping['meal_info']['meal'].title()}")
            report.append(f"  - Type: {mapping['meal_info']['type'].title()}")
        report.append("")

        # YAML generation
        report.append(f"## Generated YAML Files: {len(self.generated_yaml_files)}")
        for yaml_file in self.generated_yaml_files:
            report.append(f"- {yaml_file.name}")
        report.append("")

        # Time-based files
        report.append(f"## Created Time-Based Files: {len(self.created_time_based_files)}")
        for time_file in self.created_time_based_files:
            report.append(f"- {time_file.name}")
        report.append("")

        # Summary
        report.append("## Summary")
        report.append(f"- Files mapped: {len(self.mapped_files)}")
        report.append(f"- YAML files generated: {len(self.generated_yaml_files)}")
        report.append(f"- Time-based files created: {len(self.created_time_based_files)}")
        report.append("")
        report.append("## Next Steps")
        report.append("- The renaming system should now find the time-based files")
        report.append("- YAML files are available for all recipes")
        report.append("- Mapping data is saved for future reference")

        return "\n".join(report)

    def run(self) -> str:
        """Execute the complete mapping process."""
        print("🚀 Starting Meal Plan Mapping Process...")
        print("")

        # Ensure cooking directory exists
        self.cooking_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Process HTML files
        print("📁 Step 1: Processing HTML files and extracting meal information")
        self.process_html_files()
        print("")

        # Step 2: Save mapping
        print("💾 Step 2: Saving mapping data")
        self.save_mapping()
        print("")

        # Step 3: Generate report
        print("📊 Step 3: Generating comprehensive report")
        report = self.generate_report()

        # Save report
        report_path = self.project_root / "meal_plan_mapping_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"  ✅ Report saved to: {report_path}")
        print("")
        print("🎉 Meal Plan Mapping Process Complete!")

        return report


def main():
    """Main function to run the meal plan mapper."""
    project_root = "/Users/fjacquet/Projects/crews/epic_news"

    mapper = MealPlanMapper(project_root)
    report = mapper.run()

    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    main()
