#!/usr/bin/env python3
"""
Debug script to test holiday plan JSON to HTML conversion.

This script takes the existing itinerary.json file and uses TemplateManager.render_report
to generate HTML, helping us debug parsing and rendering issues.
"""

import json
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from epic_news.utils.html.template_manager import TemplateManager


def main():
    """Main debug function."""

    # Configuration
    input_json_file = "output/travel_guides/complete_holiday_plan.json"
    output_html_file = "output/travel_guides/complete_holiday_plan_debug.html"

    # File paths
    json_file = Path(input_json_file)
    html_file = Path(output_html_file)

    print("🔍 Debug Holiday Plan HTML Conversion")
    print(f"📄 Input JSON: {json_file}")
    print(f"🌐 Output HTML: {html_file}")
    print("-" * 50)

    # Check if JSON file exists
    if not json_file.exists():
        print(f"❌ ERROR: JSON file not found: {json_file}")
        return 1

    try:
        # Read the JSON file
        print("📖 Reading JSON file...")
        with open(json_file, encoding="utf-8") as f:
            json_data = json.load(f)

        print("✅ JSON loaded successfully")
        print(f"🔍 JSON keys: {list(json_data.keys())}")
        print(f"🔍 JSON size: {len(json.dumps(json_data))} characters")

        # Render using TemplateManager
        print("\n🔧 Rendering with TemplateManager...")
        tm = TemplateManager()
        html_content = tm.render_report("HOLIDAY_PLANNER", json_data)
        html_file.write_text(html_content, encoding="utf-8")

        print("✅ HTML generated successfully!")
        print(f"📏 HTML length: {len(html_content)} characters")
        print(f"💾 HTML saved to: {html_file}")

        # Show a preview of the HTML content
        print("\n📋 HTML Preview (first 500 chars):")
        print("-" * 30)
        print(html_content[:500])
        print("-" * 30)

        # Check if HTML file was created
        if html_file.exists():
            file_size = html_file.stat().st_size
            print(f"✅ HTML file created: {file_size} bytes")
        else:
            print("❌ HTML file was not created")

        return 0

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"❌ ERROR type: {type(e).__name__}")
        import traceback

        print("📍 Traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
