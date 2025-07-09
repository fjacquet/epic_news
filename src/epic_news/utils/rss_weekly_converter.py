"""Converter utilities for RSS Weekly reports."""

import re
from datetime import datetime

from bs4 import BeautifulSoup

from src.epic_news.models.rss_weekly_models import RssWeeklyReport


def html_to_rss_weekly_json(html_content: str) -> dict:
    """
    Convert RSS weekly HTML report to JSON format.

    This function parses HTML content and extracts structured data
    that can be used to create an RssWeeklyReport model.

    Args:
        html_content: HTML content string to parse

    Returns:
        Dictionary containing structured RSS weekly data
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title
        title_elem = soup.find("h1") or soup.find("title")
        title = title_elem.get_text().strip() if title_elem else "Résumé Hebdomadaire des Flux RSS"

        # Extract executive summary
        summary = ""
        summary_section = soup.find("section", class_="executive-summary")
        if summary_section:
            summary_p = summary_section.find("p")
            if summary_p:
                summary = summary_p.get_text().strip()

        # Extract feed digests
        feeds = []
        feed_sections = soup.find_all("div", class_="feed-digest")

        for feed_section in feed_sections:
            # Extract feed name and URL
            feed_name_elem = feed_section.find("h3")
            feed_name = feed_name_elem.get_text().strip() if feed_name_elem else "Source inconnue"
            # Remove emoji from feed name
            feed_name = re.sub(r"🌐\s*", "", feed_name)

            feed_url_elem = feed_section.find("a")
            feed_url = feed_url_elem.get("href", "") if feed_url_elem else ""

            # Extract articles
            articles = []
            article_sections = feed_section.find_all("article", class_="article-summary")

            for article_section in article_sections:
                # Extract article title and link
                title_elem = article_section.find("h4")
                if title_elem:
                    link_elem = title_elem.find("a")
                    if link_elem:
                        article_title = link_elem.get_text().strip()
                        article_link = link_elem.get("href", "")
                    else:
                        article_title = title_elem.get_text().strip()
                        article_link = ""
                else:
                    article_title = "Titre non disponible"
                    article_link = ""

                # Extract published date
                date_elem = article_section.find("p", class_="published-date")
                published = date_elem.get_text().strip() if date_elem else ""
                # Remove emoji from date
                published = re.sub(r"📅\s*", "", published)

                # Extract summary
                summary_elem = article_section.find("div", class_="summary")
                article_summary = ""
                if summary_elem:
                    summary_p = summary_elem.find("p")
                    if summary_p:
                        article_summary = summary_p.get_text().strip()

                articles.append(
                    {
                        "title": article_title,
                        "link": article_link,
                        "published": published,
                        "summary": article_summary,
                        "source_feed": feed_url,
                    }
                )

            feeds.append(
                {
                    "feed_url": feed_url,
                    "feed_name": feed_name,
                    "articles": articles,
                    "total_articles": len(articles),
                }
            )

        # Calculate totals
        total_feeds = len(feeds)
        total_articles = sum(len(feed["articles"]) for feed in feeds)

        return {
            "title": title,
            "generation_date": datetime.now().isoformat(),
            "feeds": feeds,
            "total_feeds": total_feeds,
            "total_articles": total_articles,
            "summary": summary,
        }

    except Exception as e:
        print(f"❌ Error converting HTML to RSS weekly JSON: {e}")
        return {
            "title": "Erreur de Conversion",
            "generation_date": datetime.now().isoformat(),
            "feeds": [],
            "total_feeds": 0,
            "total_articles": 0,
            "summary": f"Erreur lors de la conversion: {str(e)}",
            "error": str(e),
        }


def json_to_rss_weekly_model(json_data: dict) -> RssWeeklyReport:
    """
    Convert JSON data to RssWeeklyReport Pydantic model.

    Args:
        json_data: Dictionary containing RSS weekly data

    Returns:
        RssWeeklyReport model instance
    """
    try:
        return RssWeeklyReport.model_validate(json_data)
    except Exception as e:
        print(f"❌ Error creating RssWeeklyReport model: {e}")
        return RssWeeklyReport(
            title="Erreur de Modélisation", summary=f"Erreur lors de la création du modèle: {str(e)}"
        )


def html_to_rss_weekly_model(html_content: str) -> RssWeeklyReport:
    """
    Convert HTML content directly to RssWeeklyReport model.

    Args:
        html_content: HTML content string to parse

    Returns:
        RssWeeklyReport model instance
    """
    json_data = html_to_rss_weekly_json(html_content)
    return json_to_rss_weekly_model(json_data)
