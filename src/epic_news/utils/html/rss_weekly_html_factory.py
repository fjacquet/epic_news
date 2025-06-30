"""HTML factory for RSS Weekly digest reports."""

import json

from src.epic_news.models.rss_weekly_models import RssWeeklyReport
from src.epic_news.utils.html.template_manager import TemplateManager


def rss_weekly_to_html(crew_output, topic: str | None = None, html_file: str | None = None) -> str:
    """
    Convert RSS weekly crew output to HTML using TemplateManager.

    Args:
        crew_output: CrewAI output containing RSS weekly digest data
        topic: Optional topic for the report
        html_file: Optional path to save HTML file

    Returns:
        Complete HTML string
    """
    try:
        # Extract and parse the RSS weekly data
        if isinstance(crew_output, RssWeeklyReport):
            # Direct RssWeeklyReport object (from main.py)
            rss_model = crew_output
            print(f"✅ Using direct RssWeeklyReport object: {rss_model.title}")
        elif hasattr(crew_output, "output") and isinstance(crew_output.output, RssWeeklyReport):
            rss_model = crew_output.output
            print(f"✅ Using RssWeeklyReport from crew_output.output: {rss_model.title}")
        elif hasattr(crew_output, "raw"):
            # Try to parse raw output as JSON
            try:
                raw_data = json.loads(crew_output.raw)
                rss_model = RssWeeklyReport.model_validate(raw_data)
                print(f"✅ Parsed RssWeeklyReport from raw JSON: {rss_model.title}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error parsing RSS weekly raw output: {e}")
                # Create a minimal model with error info
                rss_model = RssWeeklyReport(
                    title="Erreur de Parsing RSS Weekly",
                    summary=f"Erreur lors du parsing des données: {str(e)}",
                )
        else:
            # Fallback: try to validate crew_output directly
            print(f"⚠️ Fallback validation for crew_output type: {type(crew_output)}")
            try:
                # If it's a pydantic model (even from a duplicate import), dump it to a dict first
                data_dict = crew_output.model_dump()
                rss_model = RssWeeklyReport.model_validate(data_dict)
                print("✅ Successfully validated from model_dump() fallback.")
            except (AttributeError, ValueError):
                # If not, try to validate directly (for raw dict inputs)
                rss_model = RssWeeklyReport.model_validate(crew_output)

        # Prepare structured data for TemplateManager
        content_data = {
            "title": rss_model.title,
            "topic": topic or "rss-weekly-digest",
            "generation_date": rss_model.generation_date.strftime("%Y-%m-%d %H:%M:%S"),
            "executive_summary": rss_model.summary,
            # RSS-specific data
            "feeds": [
                {
                    "feed_url": feed.feed_url,
                    "feed_name": feed.feed_name or _extract_domain_name(feed.feed_url),
                    "articles": [
                        {
                            "title": article.title,
                            "link": article.link,
                            "published": article.published,
                            "summary": article.summary,
                            "source_feed": article.source_feed,
                        }
                        for article in feed.articles
                    ],
                    "total_articles": feed.total_articles,
                }
                for feed in rss_model.feeds
            ],
            # Metadata
            "total_feeds": rss_model.total_feeds,
            "total_articles": rss_model.total_articles,
            "report_type": "RSS_WEEKLY",
        }

        # Generate HTML using TemplateManager
        template_manager = TemplateManager()
        html_content = template_manager.render_report("RSS_WEEKLY", content_data)

        # Optionally save to file
        if html_file:
            try:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"✅ RSS weekly HTML report saved to: {html_file}")
            except Exception as e:
                print(f"❌ Error saving RSS weekly HTML file: {e}")

        return html_content

    except Exception as e:
        print(f"❌ Error in rss_weekly_to_html: {e}")
        # Return a basic error HTML
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Erreur RSS Weekly</title>
        </head>
        <body>
            <h1>Erreur lors de la génération du rapport RSS Weekly</h1>
            <p>Une erreur s'est produite: {e}</p>
            <pre>{str(crew_output)[:1000]}...</pre>
        </body>
        </html>
        """


def _extract_domain_name(url: str) -> str:
    """Extract a readable domain name from a URL."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.title()
    except Exception:
        return url
