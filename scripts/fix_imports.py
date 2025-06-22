#!/usr/bin/env python3
"""
Script to find and fix BaseTool imports across the project.
Changes 'from crewai_tools import BaseTool' to 'from crewai.tools import BaseTool'
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path):
    """Fix BaseTool imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Define the patterns to search for
    patterns = [
        r'from\s+crewai_tools\s+import\s+BaseTool(\s*#.*)?$',
        r'from\s+crewai_tools\s+import\s+(\w+,\s+)*BaseTool(,\s+\w+)*(\s*#.*)?$',
    ]

    # Keep track if file was modified
    modified = False

    # Process the file content
    for pattern in patterns:
        # Search for the pattern in the content
        matches = re.finditer(pattern, content, re.MULTILINE)

        # Process each match
        for match in matches:
            old_import = match.group(0)
            # Create the replacement import
            if 'import BaseTool' in old_import:
                new_import = old_import.replace('crewai_tools', 'crewai.tools')
            else:
                # Handle more complex imports with multiple items
                new_import = old_import.replace('crewai_tools', 'crewai.tools')

            # Replace the import in the content
            content = content.replace(old_import, new_import)
            modified = True
            print(f"  Fixed: {old_import.strip()} -> {new_import.strip()}")

    # Write the modified content back to the file if changes were made
    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        return True

    return False


def find_and_fix_imports(directory):
    """Find and fix BaseTool imports in all Python files in the directory."""
    fixed_files = 0

    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f"Checking {file_path}")
                if fix_imports_in_file(file_path):
                    fixed_files += 1

    return fixed_files


if __name__ == "__main__":
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src" / "epic_news"

    print(f"Looking for BaseTool imports to fix in {src_dir}...")
    fixed_count = find_and_fix_imports(src_dir)

    print(f"\nFixed imports in {fixed_count} files.")
    if fixed_count > 0:
        print("Please run your tests to ensure everything works correctly.")
    else:
        print("No files needed fixing.")
