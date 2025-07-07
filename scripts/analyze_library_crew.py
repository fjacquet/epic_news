#!/usr/bin/env python3
"""
Analyze LibraryCrew output and diagnose issues.

This script examines the output files of the LibraryCrew and provides diagnostics
on structure, content, and templating issues.
"""

import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
from loguru import logger

# Set up logging
# logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
# logger = logging.getLogger("library_analyzer")

# Find the project root (assuming we're in scripts)
project_root = Path(__file__).resolve().parent.parent.parent.parent


def analyze_html_file(html_path):
    """Analyze HTML output file for issues."""
    logger.info(f"Analyzing HTML file: {html_path}")

    if not os.path.exists(html_path):
        logger.error(f"HTML file not found: {html_path}")
        return

    try:
        with open(html_path, encoding="utf-8") as f:
            content = f.read()

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")

        # Basic structure check
        logger.info("Checking HTML structure...")

        # Check for <!DOCTYPE html> declaration
        if "<!DOCTYPE html>" not in content and "<!doctype html>" not in content.lower():
            logger.warning("Missing DOCTYPE declaration")

        # Check for head and meta tags
        head = soup.head
        if not head:
            logger.warning("Missing <head> element")
        else:
            if not head.find("meta", attrs={"charset": True}):
                logger.warning("Missing charset meta tag")
            if not head.find("meta", attrs={"name": "viewport"}):
                logger.warning("Missing viewport meta tag")
            if not head.find("title"):
                logger.warning("Missing title tag")

        # Check for proper CSS usage
        styles = soup.find_all("style")
        css_links = soup.find_all("link", rel="stylesheet")
        if not styles and not css_links:
            logger.warning("No styling found (neither <style> nor CSS link)")

        # Check content
        logger.info("Analyzing content...")
        text_content = soup.get_text()

        # Check for "Art of War" references
        if "art of war" not in text_content.lower() and "sun tzu" not in text_content.lower():
            logger.warning("Content does not appear to be about 'Art of War' by Sun Tzu")

        # Check for structure
        sections = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if len(sections) < 3:
            logger.warning(f"Few sections found, structure may be minimal ({len(sections)} headings)")

        # Check for template usage
        template_patterns = [
            r'class="epic-news-report"',
            r'class="report-container"',
            r'class="report-header"',
            r'class="report-section"',
        ]

        template_matches = 0
        for pattern in template_patterns:
            if re.search(pattern, content):
                template_matches += 1

        template_usage = (template_matches / len(template_patterns)) * 100
        if template_usage < 50:
            logger.warning(
                f"Low template usage indicator: {template_usage:.1f}% of expected template patterns"
            )
        else:
            logger.info(f"Template usage looks good: {template_usage:.1f}%")

        logger.info("HTML content summary:")
        word_count = len(text_content.split())
        logger.info(f"- Word count: {word_count}")
        logger.info(f"- Number of headings: {len(sections)}")
        logger.info(f"- Number of paragraphs: {len(soup.find_all('p'))}")
        logger.info(f"- Number of links: {len(soup.find_all('a'))}")

        # Print first few lines for inspection
        logger.info("HTML beginning (first 500 characters):")
        print(content[:500] + "...")

    except Exception as e:
        logger.error(f"Error analyzing HTML: {str(e)}")


def analyze_file_paths():
    """Check for file path issues in the output."""
    logger.info("Analyzing file paths...")

    # Define expected and incorrect paths
    expected_path = os.path.join(project_root, "output", "library")
    incorrect_path = os.path.join(
        project_root, "Users", "fjacquet", "Projects", "crews", "epic_news", "output", "library"
    )

    # Check if incorrect path exists
    if os.path.exists(incorrect_path):
        logger.warning(f"Found incorrect nested path: {incorrect_path}")
        if os.path.isfile(os.path.join(incorrect_path, "book_summary.pdf")):
            logger.warning("PDF file exists in the incorrect location")

    # Check for files in correct path
    if os.path.exists(expected_path):
        files = os.listdir(expected_path)
        logger.info(f"Files in correct output directory: {files}")


def analyze_templates_directory():
    """Check templates directory for expected files."""
    templates_dir = os.path.join(project_root, "templates")
    logger.info(f"Analyzing templates directory: {templates_dir}")

    if not os.path.exists(templates_dir):
        logger.warning(f"Templates directory not found: {templates_dir}")
        return

    files = os.listdir(templates_dir)
    logger.info(f"Templates available: {files}")

    report_template = os.path.join(templates_dir, "report_template.html")
    if not os.path.exists(report_template):
        logger.warning(f"Report template not found: {report_template}")
    else:
        logger.info(f"Report template exists: {report_template}")


def analyze_dashboard_directories():
    """Examine dashboard directories setup."""
    dashboard_data = os.path.join(project_root, "output", "dashboard_data")
    dashboards = os.path.join(project_root, "output", "dashboards")

    logger.info("Analyzing dashboard directories...")

    if not os.path.exists(dashboard_data):
        logger.warning(f"Dashboard data directory doesn't exist: {dashboard_data}")
    else:
        files = os.listdir(dashboard_data)
        logger.info(f"Dashboard data files: {files}")

    if not os.path.exists(dashboards):
        logger.warning(f"Dashboards directory doesn't exist: {dashboards}")
    else:
        files = os.listdir(dashboards)
        logger.info(f"Dashboard files: {files}")


def main():
    """Main function to analyze LibraryCrew output."""
    logger.info("Starting LibraryCrew output analysis...")

    # Analyze HTML file
    html_path = os.path.join(project_root, "output", "library", "book_summary.html")
    analyze_html_file(html_path)

    # Analyze file paths
    analyze_file_paths()

    # Check templates directory
    analyze_templates_directory()

    # Check dashboard directories
    analyze_dashboard_directories()

    logger.info("Analysis complete.")


if __name__ == "__main__":
    main()
