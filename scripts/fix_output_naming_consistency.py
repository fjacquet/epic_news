#!/usr/bin/env python3
"""
Output Naming Consistency Fix

This script fixes the mess in output/cooking/ by:
1. Standardizing all filenames to proper slugged format
2. Ensuring every HTML file has a corresponding YAML file
3. Extracting recipe information from HTML to generate missing YAML files
4. Creating a consistent, production-ready file organization
"""

import re
from pathlib import Path

import yaml
from bs4 import BeautifulSoup


class OutputNamingFixer:
    """Fixes naming consistency and pairing in output/cooking directory."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.output_dir = self.project_root / "output" / "cooking"
        self.backup_dir = self.output_dir / "backup"
        self.fixes_applied = []
        self.issues_found = []

    def create_backup(self):
        """Create backup of current files before making changes."""
        print("📦 Creating backup of current files...")
        self.backup_dir.mkdir(exist_ok=True)

        for file_path in self.output_dir.glob("*"):
            if file_path.is_file() and file_path.name != "backup":
                backup_path = self.backup_dir / file_path.name
                backup_path.write_bytes(file_path.read_bytes())
                print(f"   Backed up: {file_path.name}")

    def slugify_filename(self, filename: str) -> str:
        """Convert filename to proper slug format."""
        # Remove file extension
        name = Path(filename).stem

        # Convert to lowercase
        name = name.lower()

        # Replace spaces and special characters with hyphens
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"[-\s]+", "-", name)

        # Remove leading/trailing hyphens
        return name.strip("-")

    def extract_recipe_info_from_html(self, html_path: Path) -> dict:
        """Extract recipe information from HTML file."""
        try:
            with open(html_path, encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")

            # Extract title
            title_elem = soup.find("h1") or soup.find("title")
            title = title_elem.get_text().strip() if title_elem else html_path.stem.replace("-", " ").title()

            # Extract ingredients
            ingredients = []
            ingredient_lists = soup.find_all(["ul", "ol"])
            for ul in ingredient_lists:
                # Look for ingredient-like content
                items = ul.find_all("li")
                if items and len(items) > 2:  # Likely an ingredient list
                    for li in items:
                        ingredient_text = li.get_text().strip()
                        if ingredient_text and len(ingredient_text) > 3:
                            ingredients.append(ingredient_text)
                    break  # Take first substantial list

            # Extract directions
            directions = []
            # Look for ordered lists (instructions)
            for ol in soup.find_all("ol"):
                items = ol.find_all("li")
                if items:
                    for li in items:
                        direction_text = li.get_text().strip()
                        if direction_text:
                            directions.append(direction_text)
                    break  # Take first ordered list

            # If no ordered list, look for paragraphs that might be instructions
            if not directions:
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and (
                        "étape" in text.lower() or "mélanger" in text.lower() or "cuire" in text.lower()
                    ):
                        directions.append(text)

            # Extract other info
            description = ""
            first_p = soup.find("p")
            if first_p:
                description = first_p.get_text().strip()

            return {
                "name": title,
                "description": description,
                "ingredients": ingredients,
                "directions": directions,
                "servings": "4 personnes",  # Default
                "prep_time": "30 minutes",  # Default
                "cook_time": "45 minutes",  # Default
                "difficulty": "Moyen",  # Default
                "source": "epic_news cooking crew",
                "categories": ["Plat principal"],  # Default
                "photo_url": None,
                "notes": "Recette générée par l'équipe de cuisine epic_news",
            }

        except Exception as e:
            print(f"   ⚠️ Error extracting from {html_path.name}: {str(e)}")
            return {
                "name": html_path.stem.replace("-", " ").title(),
                "description": "Délicieuse recette française",
                "ingredients": ["Ingrédients à déterminer"],
                "directions": ["Instructions à déterminer"],
                "servings": "4 personnes",
                "prep_time": "30 minutes",
                "cook_time": "45 minutes",
                "difficulty": "Moyen",
                "source": "epic_news cooking crew",
                "categories": ["Plat principal"],
                "photo_url": None,
                "notes": "Recette générée par l'équipe de cuisine epic_news",
            }

    def create_paprika_yaml(self, recipe_info: dict, yaml_path: Path):
        """Create Paprika-compatible YAML file."""
        paprika_recipe = {
            "name": recipe_info["name"],
            "description": recipe_info["description"],
            "ingredients": recipe_info["ingredients"],
            "directions": recipe_info["directions"],
            "servings": recipe_info["servings"],
            "prep_time": recipe_info["prep_time"],
            "cook_time": recipe_info["cook_time"],
            "difficulty": recipe_info["difficulty"],
            "source": recipe_info["source"],
            "source_url": None,
            "image_url": recipe_info.get("photo_url"),
            "categories": recipe_info["categories"],
            "cuisine": "Française",
            "course": "Plat principal",
            "method": "Thermomix optimisé",
            "rating": 5,
            "notes": recipe_info["notes"],
            "nutritional_info": "Information nutritionnelle à déterminer",
            "created": None,
            "hash": None,
            "photo": None,
            "photo_hash": None,
            "scale": None,
        }

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(paprika_recipe, f, default_flow_style=False, allow_unicode=True, indent=2)

    def analyze_current_state(self) -> dict:
        """Analyze current state of output directory."""
        print("🔍 Analyzing current state...")

        html_files = list(self.output_dir.glob("*.html"))
        yaml_files = list(self.output_dir.glob("*.yaml"))

        analysis = {
            "html_files": [f.name for f in html_files],
            "yaml_files": [f.name for f in yaml_files],
            "html_count": len(html_files),
            "yaml_count": len(yaml_files),
            "paired_files": [],
            "orphaned_html": [],
            "orphaned_yaml": [],
            "naming_issues": [],
        }

        # Check for pairs and orphans
        for html_file in html_files:
            html_stem = html_file.stem
            yaml_counterpart = self.output_dir / f"{html_stem}.yaml"

            if yaml_counterpart.exists():
                analysis["paired_files"].append(html_stem)
            else:
                analysis["orphaned_html"].append(html_file.name)

        for yaml_file in yaml_files:
            yaml_stem = yaml_file.stem
            html_counterpart = self.output_dir / f"{yaml_stem}.html"

            if not html_counterpart.exists():
                analysis["orphaned_yaml"].append(yaml_file.name)

        # Check naming consistency
        for file_path in html_files + yaml_files:
            filename = file_path.name
            slugged_name = self.slugify_filename(filename)

            if file_path.stem != slugged_name:
                analysis["naming_issues"].append(
                    {"current": filename, "should_be": f"{slugged_name}{file_path.suffix}"}
                )

        return analysis

    def fix_naming_and_pairing(self):
        """Fix all naming and pairing issues."""
        print("🔧 Fixing naming and pairing issues...")

        # Get current HTML files
        html_files = list(self.output_dir.glob("*.html"))

        # Process each HTML file
        for html_file in html_files:
            print(f"\n📄 Processing: {html_file.name}")

            # Generate proper slugged name
            slugged_name = self.slugify_filename(html_file.name)
            new_html_name = f"{slugged_name}.html"
            new_yaml_name = f"{slugged_name}.yaml"

            new_html_path = self.output_dir / new_html_name
            new_yaml_path = self.output_dir / new_yaml_name

            # Rename HTML file if needed
            if html_file.name != new_html_name:
                print(f"   🔄 Renaming HTML: {html_file.name} → {new_html_name}")
                html_file.rename(new_html_path)
                self.fixes_applied.append(f"Renamed HTML: {html_file.name} → {new_html_name}")
            else:
                new_html_path = html_file

            # Check if YAML exists
            old_yaml_path = self.output_dir / f"{html_file.stem}.yaml"

            if old_yaml_path.exists() and old_yaml_path != new_yaml_path:
                # Rename existing YAML
                print(f"   🔄 Renaming YAML: {old_yaml_path.name} → {new_yaml_name}")
                old_yaml_path.rename(new_yaml_path)
                self.fixes_applied.append(f"Renamed YAML: {old_yaml_path.name} → {new_yaml_name}")
            elif not new_yaml_path.exists():
                # Create missing YAML
                print(f"   ➕ Creating missing YAML: {new_yaml_name}")
                recipe_info = self.extract_recipe_info_from_html(new_html_path)
                self.create_paprika_yaml(recipe_info, new_yaml_path)
                self.fixes_applied.append(f"Created missing YAML: {new_yaml_name}")
            else:
                print(f"   ✅ YAML already exists: {new_yaml_name}")

    def cleanup_orphaned_files(self):
        """Remove any orphaned files that don't have pairs."""
        print("\n🧹 Cleaning up orphaned files...")

        # Find orphaned YAML files (YAML without corresponding HTML)
        yaml_files = list(self.output_dir.glob("*.yaml"))

        for yaml_file in yaml_files:
            html_counterpart = self.output_dir / f"{yaml_file.stem}.html"
            if not html_counterpart.exists():
                print(f"   🗑️ Removing orphaned YAML: {yaml_file.name}")
                yaml_file.unlink()
                self.fixes_applied.append(f"Removed orphaned YAML: {yaml_file.name}")

    def generate_report(self):
        """Generate a comprehensive fix report."""
        print("\n" + "=" * 60)
        print("📊 OUTPUT NAMING CONSISTENCY FIX REPORT")
        print("=" * 60)

        # Final state analysis
        final_analysis = self.analyze_current_state()

        print("\n📈 FINAL STATE:")
        print(f"   HTML Files: {final_analysis['html_count']}")
        print(f"   YAML Files: {final_analysis['yaml_count']}")
        print(f"   Paired Files: {len(final_analysis['paired_files'])}")
        print(f"   Orphaned HTML: {len(final_analysis['orphaned_html'])}")
        print(f"   Orphaned YAML: {len(final_analysis['orphaned_yaml'])}")
        print(f"   Naming Issues: {len(final_analysis['naming_issues'])}")

        if final_analysis["paired_files"]:
            print("\n✅ PROPERLY PAIRED FILES:")
            for pair in final_analysis["paired_files"]:
                print(f"   📄 {pair}.html ↔️ {pair}.yaml")

        if self.fixes_applied:
            print(f"\n🔧 FIXES APPLIED ({len(self.fixes_applied)}):")
            for fix in self.fixes_applied:
                print(f"   ✅ {fix}")

        if final_analysis["naming_issues"]:
            print("\n⚠️ REMAINING NAMING ISSUES:")
            for issue in final_analysis["naming_issues"]:
                print(f"   ❌ {issue['current']} should be {issue['should_be']}")

        # Success determination
        is_clean = (
            len(final_analysis["orphaned_html"]) == 0
            and len(final_analysis["orphaned_yaml"]) == 0
            and len(final_analysis["naming_issues"]) == 0
            and final_analysis["html_count"] == final_analysis["yaml_count"]
        )

        if is_clean:
            print("\n🎉 OUTPUT DIRECTORY IS NOW CLEAN AND CONSISTENT! ✅")
        else:
            print("\n⚠️ Some issues remain - manual review may be needed")

        print("\n" + "=" * 60)

        return is_clean

    def run_fix(self):
        """Run the complete naming consistency fix."""
        print("🚀 Starting Output Naming Consistency Fix...\n")

        # Initial analysis
        initial_analysis = self.analyze_current_state()
        print("📊 INITIAL STATE:")
        print(f"   HTML Files: {initial_analysis['html_count']}")
        print(f"   YAML Files: {initial_analysis['yaml_count']}")
        print(f"   Orphaned HTML: {len(initial_analysis['orphaned_html'])}")
        print(f"   Orphaned YAML: {len(initial_analysis['orphaned_yaml'])}")
        print(f"   Naming Issues: {len(initial_analysis['naming_issues'])}")

        if initial_analysis["orphaned_html"]:
            print("\n❌ ORPHANED HTML FILES:")
            for orphan in initial_analysis["orphaned_html"]:
                print(f"   📄 {orphan}")

        if initial_analysis["naming_issues"]:
            print("\n❌ NAMING ISSUES:")
            for issue in initial_analysis["naming_issues"]:
                print(f"   🔄 {issue['current']} → {issue['should_be']}")

        # Create backup
        self.create_backup()

        # Apply fixes
        self.fix_naming_and_pairing()
        self.cleanup_orphaned_files()

        # Generate report
        return self.generate_report()


def main():
    """Main function to run the output naming consistency fix."""
    fixer = OutputNamingFixer()
    success = fixer.run_fix()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
