#!/usr/bin/env python3
"""
Test script for enhanced JSON repair mechanism.
"""

import json
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.epic_news.utils.debug_utils import _attempt_json_repair


def test_json_repair():
    """Test various JSON repair scenarios."""

    test_cases = [
        # Missing colon after key
        ('{"key" "value"}', '{"key": "value"}'),

        # Missing quotes around key
        ('{key: "value"}', '{"key": "value"}'),

        # Missing quotes around string value
        ('{"key": value}', '{"key": "value"}'),

        # Trailing comma
        ('{"key": "value",}', '{"key": "value"}'),

        # Missing closing brace
        ('{"key": "value"', '{"key": "value"}'),

        # Complex case with multiple issues
        ('{title "Test Article", description: content, "tags": ["tag1", "tag2",]}',
         '{"title": "Test Article", "description": "content", "tags": ["tag1", "tag2"]}'),
    ]

    print("🧪 Testing JSON repair mechanism...")

    for i, (broken_json, _expected_pattern) in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input:    {broken_json}")

        try:
            repaired = _attempt_json_repair(broken_json)
            print(f"Repaired: {repaired}")

            # Try to parse the repaired JSON
            parsed = json.loads(repaired)
            print(f"✅ Successfully parsed: {parsed}")

        except json.JSONDecodeError as e:
            print(f"❌ Still invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    print("\n🎯 Testing with realistic LLM output...")

    # Simulate a realistic malformed JSON from LLM
    realistic_broken = '''
    {
        "destination": "Paris",
        "duration" "5 days",
        "activities": [
            {
                title: "Visit Eiffel Tower",
                "description": "Iconic landmark visit",
                "time": "Morning"
            },
            {
                "title": "Louvre Museum"
                "description": museum visit,
                "time": "Afternoon",
            }
        ],
        "restaurants": [
            {"name": "Le Comptoir", "cuisine": "French"}
        ]
    '''

    print(f"Realistic input: {realistic_broken[:100]}...")

    try:
        repaired = _attempt_json_repair(realistic_broken)
        parsed = json.loads(repaired)
        print("✅ Successfully repaired realistic LLM JSON!")
        print(f"Parsed keys: {list(parsed.keys())}")

    except Exception as e:
        print(f"❌ Failed to repair realistic JSON: {e}")

if __name__ == "__main__":
    test_json_repair()
