"""
Utility functions for handling file operations.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def read_file_content(file_path):
    """
    Read the content of a file and return it as a string.

    Args:
        file_path (str): Path to the file (absolute or relative)

    Returns:
        str: The content of the file as a string
    """
    # Handle both absolute and relative paths
    if not os.path.isabs(file_path):
        # If relative path, make it relative to the project root
        file_path = os.path.normpath(os.path.join(os.getcwd(), file_path))

    try:
        with open(file_path, encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"Error: File not found at path: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return ""


def save_json_file(file_path: str, data: dict):
    """
    Save a dictionary to a JSON file.

    Args:
        file_path (str): The path to the JSON file.
        data (dict): The dictionary to save.
    """
    path = Path(file_path)
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def ensure_output_directory(directory_path: str):
    """
    Ensures that the specified output directory exists, creating it if necessary.
    
    Args:
        directory_path (str): The path to the directory to ensure exists.
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
