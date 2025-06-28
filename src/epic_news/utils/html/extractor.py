"""Utility to extract HTML from CrewAI JSON-wrapped outputs."""

import json
from pathlib import Path
from typing import Union


def extract_html_from_json_output(file_path: Union[str, Path]) -> bool:
    """
    Extract HTML content from CrewAI JSON-wrapped output and save as pure HTML.

    Args:
        file_path: Path to the JSON-wrapped HTML file

    Returns:
        bool: True if extraction successful, False otherwise
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        # Read the JSON-wrapped content
        content = file_path.read_text(encoding="utf-8")

        # Try to parse as JSON
        try:
            data = json.loads(content)

            # Extract HTML from report_body or html field
            html_content = None
            if isinstance(data, dict):
                if "report_body" in data:
                    html_content = data["report_body"]
                elif "html" in data:
                    html_content = data["html"]

                if html_content:
                    # Write pure HTML back to the same file
                    file_path.write_text(html_content, encoding="utf-8")
                    print(f"✅ Extracted HTML from JSON wrapper: {file_path}")
                    return True

            print(f"⚠️  No report_body or html field found in JSON: {file_path}")
            return False

        except json.JSONDecodeError:
            # File is not JSON, assume it's already HTML
            if content.strip().startswith("<!DOCTYPE html>"):
                print(f"✅ File is already pure HTML: {file_path}")
                return True
            print(f"⚠️  File is neither JSON nor HTML: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error processing file {file_path}: {e}")
        return False


def extract_html_from_directory(directory_path: Union[str, Path], pattern: str = "*.html") -> int:
    """
    Extract HTML from all JSON-wrapped files in a directory.

    Args:
        directory_path: Directory to process
        pattern: File pattern to match (default: "*.html")

    Returns:
        int: Number of files successfully processed
    """
    directory_path = Path(directory_path)

    if not directory_path.exists():
        print(f"❌ Directory not found: {directory_path}")
        return 0

    processed = 0
    for file_path in directory_path.glob(pattern):
        if extract_html_from_json_output(file_path):
            processed += 1

    print(f"✅ Processed {processed} files in {directory_path}")
    return processed


if __name__ == "__main__":
    # Example usage
    extract_html_from_json_output("output/shopping_advisor/shopping_advice.html")
