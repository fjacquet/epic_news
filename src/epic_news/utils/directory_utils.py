"""
Utility functions for directory management in Epic News application.
"""

import os


def ensure_output_directory(relative_path: str) -> str:
    """
    Ensure a specific output directory exists and return its path.

    Args:
        relative_path: Path relative to the project root (e.g., 'output/cooking')

    Returns:
        The path to the created directory
    """
    os.makedirs(relative_path, exist_ok=True)
    return relative_path


def ensure_output_directories():
    """
    Ensure all required output directories exist.
    Creates the necessary directory structure for storing outputs from various crews.
    """
    # Base directories
    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # Crew-specific output directories - comprehensive list based on codebase analysis
    output_subdirs = [
        "company_profiler",
        "contact_finder",
        "cooking",
        "deep_research",
        "email",
        "geospatial_analysis",
        "holiday",
        "hr_intelligence",
        "html_designer",  # For professional HTML report generation
        "lead_scoring",
        "legal_analysis",
        "library",
        "marketing",
        "meeting",
        "menu_designer",
        "osint",
        "poem",
        "shopping_advisor",
        "tech_stack",
        "travel_guides",  # For holiday planner
        "web_presence",
    ]

    # Create all output subdirectories
    for subdir in output_subdirs:
        ensure_output_directory(f"output/{subdir}")
