#!/usr/bin/env python3
"""
Fix Cooking Files Script

This script addresses two major issues with the cooking crew output:
1. HTML files scattered at project root instead of output/cooking/
2. Missing YAML files that should accompany HTML files

The script will:
- Move all cooking-related HTML files from project root to output/cooking/
- Check for corresponding YAML files and report missing ones
- Validate HTML file structure (proper HTML5 vs JSON-wrapped)
- Generate a summary report of the fixes applied
"""

import os
import shutil
from pathlib import Path


class CookingFilesFixer:
    """Fixes cooking crew file organization and missing files."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.output_dir = self.project_root / "output" / "cooking"
        self.moved_files = []
        self.missing_yaml_files = []
        self.json_wrapped_files = []
        self.proper_html_files = []

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_cooking_related_html(self, file_path: Path) -> bool:
        """Check if an HTML file is cooking/recipe related."""
        cooking_keywords = [
            "thermomix",
            "recette",
            "cuisine",
            "plat",
            "entree",
            "dessert",
            "couscous",
            "blanquette",
            "bourguignon",
            "tarte",
            "gateau",
            "poulet",
            "boeuf",
            "saumon",
            "veloute",
            "soupe",
            "salade",
            "oeufs",
            "quiche",
            "flan",
            "jambalaya",
            "tajine",
            "escalopes",
            "hachis",
            "gougeres",
            "bugnes",
            "alevropita",
            "dinde",
            "coq",
        ]

        filename_lower = file_path.name.lower()
        return any(keyword in filename_lower for keyword in cooking_keywords)

    def check_html_structure(self, file_path: Path) -> str:
        """Check if HTML file has proper structure or is JSON-wrapped."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read().strip()

            # Check if it's JSON-wrapped
            if content.startswith('{"html":"') and content.endswith('"}'):
                return "json_wrapped"
            if content.startswith("<!DOCTYPE html>"):
                return "proper_html5"
            if content.startswith("<html"):
                return "html_no_doctype"
            return "unknown_format"
        except Exception as e:
            return f"error: {e}"

    def find_cooking_html_files(self) -> list[Path]:
        """Find all cooking-related HTML files at project root."""
        html_files = []

        for file_path in self.project_root.glob("*.html"):
            if self.is_cooking_related_html(file_path):
                html_files.append(file_path)

        return html_files

    def move_html_files(self) -> None:
        """Move cooking HTML files from project root to output/cooking/."""
        cooking_files = self.find_cooking_html_files()

        print(f"🔍 Found {len(cooking_files)} cooking-related HTML files at project root")

        for file_path in cooking_files:
            destination = self.output_dir / file_path.name

            # Check HTML structure before moving
            structure = self.check_html_structure(file_path)

            try:
                # Move the file
                shutil.move(str(file_path), str(destination))
                self.moved_files.append(
                    {"original": str(file_path), "destination": str(destination), "structure": structure}
                )

                # Categorize by structure
                if structure == "json_wrapped":
                    self.json_wrapped_files.append(destination)
                elif structure in ["proper_html5", "html_no_doctype"]:
                    self.proper_html_files.append(destination)

                print(f"  ✅ Moved {file_path.name} → output/cooking/ ({structure})")

            except Exception as e:
                print(f"  ❌ Failed to move {file_path.name}: {e}")

    def check_yaml_files(self) -> None:
        """Check for missing YAML files corresponding to HTML files."""
        for html_file in self.output_dir.glob("*.html"):
            yaml_file = html_file.with_suffix(".yaml")

            if not yaml_file.exists():
                self.missing_yaml_files.append(str(yaml_file))

    def generate_report(self) -> str:
        """Generate a comprehensive report of the fixes applied."""
        report = []
        report.append("# Cooking Files Fix Report")
        report.append(f"Generated: {os.popen('date').read().strip()}")
        report.append("")

        # Files moved
        report.append(f"## Files Moved: {len(self.moved_files)}")
        for file_info in self.moved_files:
            report.append(
                f"- {Path(file_info['original']).name} → output/cooking/ ({file_info['structure']})"
            )
        report.append("")

        # HTML structure analysis
        report.append("## HTML Structure Analysis")
        report.append(f"- ✅ Proper HTML5 files: {len(self.proper_html_files)}")
        report.append(f"- ❌ JSON-wrapped files: {len(self.json_wrapped_files)}")
        report.append("")

        if self.json_wrapped_files:
            report.append("### JSON-Wrapped Files (Need Fixing)")
            for file_path in self.json_wrapped_files:
                report.append(f"- {Path(file_path).name}")
            report.append("")

        # Missing YAML files
        report.append(f"## Missing YAML Files: {len(self.missing_yaml_files)}")
        for yaml_file in self.missing_yaml_files:
            report.append(f"- {Path(yaml_file).name}")
        report.append("")

        # Summary
        report.append("## Summary")
        report.append(f"- Total files moved: {len(self.moved_files)}")
        report.append(f"- Files needing HTML structure fix: {len(self.json_wrapped_files)}")
        report.append(f"- Missing YAML files: {len(self.missing_yaml_files)}")

        return "\n".join(report)

    def run(self) -> str:
        """Execute the complete fix process."""
        print("🚀 Starting Cooking Files Fix Process...")
        print("")

        # Step 1: Move HTML files
        print("📁 Step 1: Moving HTML files to correct location")
        self.move_html_files()
        print("")

        # Step 2: Check for missing YAML files
        print("📄 Step 2: Checking for missing YAML files")
        self.check_yaml_files()
        print(f"  ⚠️ Found {len(self.missing_yaml_files)} missing YAML files")
        print("")

        # Step 3: Generate report
        print("📊 Step 3: Generating comprehensive report")
        report = self.generate_report()

        # Save report
        report_path = self.project_root / "cooking_files_fix_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"  ✅ Report saved to: {report_path}")
        print("")
        print("🎉 Cooking Files Fix Process Complete!")

        return report


def main():
    """Main function to run the cooking files fixer."""
    project_root = "/Users/fjacquet/Projects/crews/epic_news"

    fixer = CookingFilesFixer(project_root)
    report = fixer.run()

    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    main()
