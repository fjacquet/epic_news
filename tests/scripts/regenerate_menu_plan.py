import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json

from src.epic_news.utils.html.menu_html_factory import menu_to_html

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

INPUT_JSON = Path("output/menu_designer/menu_weekly_menu.json")
OUTPUT_HTML = Path("output/menu_designer/menu_weekly_menu.html")

if not INPUT_JSON.exists():
    print(f"❌ Error: Input JSON file not found at {INPUT_JSON}")
    print("Run the MenuDesigner crew first: crewai flow kickoff")
    sys.exit(1)

with INPUT_JSON.open(encoding="utf-8") as f:
    data = json.load(f)

# ---------------------------------------------------------------------------
# Re-generate HTML
# ---------------------------------------------------------------------------

menu_to_html(data, html_file=str(OUTPUT_HTML), title="Weekly Menu Plan")
print("✅ Menu HTML regenerated successfully →", OUTPUT_HTML)
