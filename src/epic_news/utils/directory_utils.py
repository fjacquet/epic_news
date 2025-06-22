"""
Utility functions for directory management in Epic News application.
"""

import os


def ensure_output_directories():
    """
    Ensure all required output directories exist.
    Creates the necessary directory structure for storing outputs from various crews.
    """
    # Base directories
    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # Crew-specific output directories
    output_subdirs = [
        "meeting",
        "lead_scoring",
        "contact_finder",
        "cooking",
        "library",
        "poem",
        "email",
        "holiday",
        "marketing",
    ]

    # Create all output subdirectories
    for subdir in output_subdirs:
        os.makedirs(f"output/{subdir}", exist_ok=True)
