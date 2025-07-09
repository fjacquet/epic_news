#!/usr/bin/env python3
"""
Script to clean all HTML reports by extracting pure HTML from JSON wrappers or action traces.
This script processes all crew output files and ensures they contain pure HTML.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our utilities
sys.path.append(str(Path(__file__).parent.parent / "src"))

from epic_news.utils.html.extractor import extract_html_from_json_output


def clean_all_reports():
    """Clean all HTML reports in the output directory."""
    output_dir = Path(__file__).parent.parent / "output"

    # List of known HTML report files
    html_files = [
        "shopping_advisor/shopping_advice.html",
        "saint_daily/report.html",
        "findaily/report.html",
        "cooking/recipe.html",
        "news_daily/report.html",
        "rss_weekly/report.html",
    ]

    cleaned_count = 0

    for html_file in html_files:
        file_path = output_dir / html_file
        if file_path.exists():
            print(f"Processing {html_file}...")
            try:
                if extract_html_from_json_output(str(file_path)):
                    print(f"✅ Cleaned {html_file}")
                    cleaned_count += 1
                else:
                    print(f"⚠️  {html_file} already clean or no HTML found")
            except Exception as e:
                print(f"❌ Error processing {html_file}: {e}")
        else:
            print(f"⚠️  {html_file} not found")

    print(f"\n🎉 Cleaned {cleaned_count} HTML reports")


if __name__ == "__main__":
    clean_all_reports()
