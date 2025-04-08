"""
Utility functions for handling file operations.
"""

import os

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
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Error: File not found at path: {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return ""
