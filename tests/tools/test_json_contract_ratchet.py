"""Ratchet: tools whose _run() doesn't produce JSON may not increase.

Static heuristic: a tool module defining _run() is compliant if its source
references a JSON-producing helper. Crude but deterministic — the point is
to freeze the legacy list so it only shrinks. Remove a file from
KNOWN_LEGACY when you fix it; never add to it.
"""

from functools import lru_cache
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "src" / "epic_news" / "tools"

JSON_MARKERS = ("json.dumps", "ensure_json_str", "model_dump_json", "to_json")

# Seeded from the state of the codebase on 2026-07-04, rescoped 2026-07-09
# after the tools-migration cleanup (Task 6) to surviving epic_news-owned
# tools only. Shrink-only.
KNOWN_LEGACY: set[str] = {
    "html_generator_tool.py",
    "html_to_pdf_tool.py",
    "render_report_tool.py",
    "reporting_tool.py",
    "universal_report_tool.py",
}


@lru_cache(maxsize=1)
def _violators() -> set[str]:
    found = set()
    for path in sorted(TOOLS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "def _run(" not in source:
            continue
        if not any(marker in source for marker in JSON_MARKERS):
            found.add(path.name)
    return found


def test_json_contract_violations_do_not_grow():
    current = _violators()
    new_violations = current - KNOWN_LEGACY
    assert not new_violations, (
        f"New tools without JSON output: {sorted(new_violations)}. "
        "New tools must return JSON strings (see tools/CLAUDE.md and _json_utils)."
    )


def test_known_legacy_list_is_honest():
    """Entries fixed in the source must be removed from KNOWN_LEGACY."""
    current = _violators()
    stale = KNOWN_LEGACY - current
    assert not stale, f"Fixed tools still listed in KNOWN_LEGACY: {sorted(stale)}"
