"""
This module provides a factory function for generating an HTML report from
a JSON file containing RSS feed data.
"""

import json
from loguru import logger
from typing import Dict, Any

from bs4 import BeautifulSoup

# Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def generate_rss_weekly_html_report(json_file_path: str, output_html_path: str):
    """
    Generates an HTML report from a JSON file containing RSS feed data.

    Args:
        json_file_path (str): The path to the input JSON file.
        output_html_path (str): The path to the output HTML file.
    """
    logger.info(f"Generating HTML report from {json_file_path}...")

    try:
        # Read the JSON data from the file
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found: {json_file_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in {json_file_path}")
        return

    # Create a new BeautifulSoup object for the HTML report
    soup = BeautifulSoup(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly RSS Summary</title>
            <style>
                body { font-family: sans-serif; line-height: 1.6; margin: 20px; }
                h1, h2 { color: #333; }
                .feed { margin-bottom: 30px; }
                .article { margin-bottom: 15px; }
                .article-title { font-size: 1.2em; font-weight: bold; }
                .article-summary { margin-top: 5px; }
            </style>
        </head>
        <body>
            <h1>Weekly RSS Summary</h1>
        </body>
        </html>
    """,
        "html.parser",
    )

    body = soup.body

    # Iterate over the feeds and articles to build the HTML content
    for feed in data.get("rss_feeds", []):
        feed_div = soup.new_tag("div", **{"class": "feed"})
        feed_title = soup.new_tag("h2")
        feed_title.string = feed.get("feed_title", "Untitled Feed")
        feed_div.append(feed_title)

        for article in feed.get("articles", []):
            article_div = soup.new_tag("div", **{"class": "article"})
            article_title = soup.new_tag("div", **{"class": "article-title"})
            article_link = soup.new_tag("a", href=article.get("link", "#"))
            article_link.string = article.get("title", "Untitled Article")
            article_title.append(article_link)
            article_div.append(article_title)

            if "summary" in article:
                summary_p = soup.new_tag("p", **{"class": "article-summary"})
                summary_p.string = article["summary"]
                article_div.append(summary_p)

            feed_div.append(article_div)

        body.append(feed_div)

    # Write the generated HTML to the output file
    try:
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        logger.info(f"HTML report successfully generated at {output_html_path}")
    except IOError as e:
        logger.error(f"Failed to write HTML report: {e}")


if __name__ == "__main__":
    # Example usage of the HTML report generator
    # This demonstrates how to create a sample JSON file and generate a report from it

    # 1. Create a sample JSON data structure
    sample_data: Dict[str, Any] = {
        "rss_feeds": [
            {
                "feed_title": "Tech News",
                "articles": [
                    {
                        "title": "The Future of AI",
                        "link": "https://example.com/ai-future",
                        "summary": "A look into the advancements in artificial intelligence.",
                    },
                    {
                        "title": "New Quantum Computing Breakthrough",
                        "link": "https://example.com/quantum-breakthrough",
                        "summary": "Scientists achieve a new milestone in quantum computing.",
                    },
                ],
            },
            {
                "feed_title": "Science Updates",
                "articles": [
                    {
                        "title": "Mars Rover Discovers New Rock Formation",
                        "link": "https://example.com/mars-discovery",
                        "summary": "The rover has found something unexpected on the red planet.",
                    }
                ],
            },
        ]
    }

    # 2. Write the sample data to a JSON file
    json_path = "output/rss_weekly/sample_rss_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)

    # 3. Generate the HTML report
    html_path = "output/rss_weekly/sample_report.html"
    generate_rss_weekly_html_report(json_path, html_path)

    print(f"Generated sample report at {html_path}")
