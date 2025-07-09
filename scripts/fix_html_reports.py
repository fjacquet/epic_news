#!/usr/bin/env python3
"""
Quick script to fix all HTML reports by extracting them from JSON wrappers.
Run this after any crew execution to ensure pure HTML output.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from epic_news.utils.html.extractor import extract_html_from_directory


def main():
    """Fix all HTML reports in output directories."""
    output_dir = Path(__file__).parent.parent / "output"

    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return

    print("🔧 Fixing HTML reports...")

    total_fixed = 0
    for crew_dir in output_dir.iterdir():
        if crew_dir.is_dir():
            print(f"📁 Processing {crew_dir.name}...")
            fixed = extract_html_from_directory(crew_dir, "*.html")
            total_fixed += fixed

    print(f"✅ Fixed {total_fixed} HTML reports total")


if __name__ == "__main__":
    main()
