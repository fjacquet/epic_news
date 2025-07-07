"""
This module provides a factory function for generating a professional HTML report
for the RSS Weekly digest based on a Pydantic model.
"""

from datetime import datetime

from bs4 import BeautifulSoup
from loguru import logger

from epic_news.models.crews.rss_weekly_report import RssWeeklyReport


def rss_weekly_to_html(report_model: RssWeeklyReport, html_file: str) -> str:
    """
    Generates and saves a professional HTML report from an RssWeeklyReport model.

    Args:
        report_model: The Pydantic model containing the report data.
        html_file: The path to save the generated HTML file.

    Returns:
        The generated HTML content as a string.
    """
    logger.info(f"🎨 Generating RSS Weekly HTML report for '{report_model.title}'...")

    soup = BeautifulSoup(
        """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report_model.title}</title>
            <style>
                :root {
                    --primary-color: #3498db;
                    --secondary-color: #2ecc71;
                    --background-color: #ecf0f1;
                    --text-color: #34495e;
                    --container-bg: #ffffff;
                    --border-color: #bdc3c7;
                }
                body.dark-mode {
                    --primary-color: #3498db;
                    --secondary-color: #2ecc71;
                    --background-color: #2c3e50;
                    --text-color: #ecf0f1;
                    --container-bg: #34495e;
                    --border-color: #7f8c8d;
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6; 
                    margin: 0;
                    padding: 0;
                    background-color: var(--background-color);
                    color: var(--text-color);
                    transition: background-color 0.3s, color 0.3s;
                }
                .container { max-width: 800px; margin: 20px auto; padding: 20px; background-color: var(--container-bg); border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1, h2, h3 { color: var(--primary-color); }
                h1 { text-align: center; border-bottom: 2px solid var(--border-color); padding-bottom: 10px; }
                h2 { border-bottom: 1px solid var(--border-color); padding-bottom: 5px; margin-top: 30px; }
                .summary { background-color: var(--background-color); padding: 15px; border-left: 5px solid var(--secondary-color); margin: 20px 0; border-radius: 5px; }
                .feed { margin-bottom: 30px; }
                .article { border: 1px solid var(--border-color); padding: 15px; margin-bottom: 15px; border-radius: 5px; }
                .article-title { font-size: 1.2em; font-weight: bold; margin-bottom: 5px; }
                .article-title a { color: var(--primary-color); text-decoration: none; }
                .article-title a:hover { text-decoration: underline; }
                .article-meta { font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; }
                .article-summary { margin-top: 10px; }
                .footer { text-align: center; margin-top: 30px; font-size: 0.8em; color: #7f8c8d; }
            </style>
        </head>
        <body>
            <div class="container">
            </div>
        </body>
        </html>
        """,
        "html.parser",
    )

    container = soup.find("div", class_="container")

    # Header
    header = soup.new_tag("h1")
    header.string = report_model.title
    container.append(header)

    # Generation Date
    date_p = soup.new_tag("p", style="text-align:center; font-style:italic;")
    date_p.string = f"Généré le: {report_model.generation_date.strftime('%d %B %Y à %H:%M')}"
    container.append(date_p)

    # Executive Summary
    if report_model.summary:
        summary_div = soup.new_tag("div", **{"class": "summary"})
        summary_header = soup.new_tag("h2")
        summary_header.string = "📝 Résumé Exécutif"
        summary_div.append(summary_header)
        summary_p = soup.new_tag("p")
        summary_p.string = report_model.summary
        summary_div.append(summary_p)
        container.append(summary_div)

    # Feeds and Articles
    for feed in report_model.feeds:
        feed_header = soup.new_tag("h2")
        feed_name = feed.feed_name or feed.feed_url
        feed_header.string = f"📡 {feed_name} ({feed.total_articles} articles)"
        container.append(feed_header)

        feed_div = soup.new_tag("div", **{"class": "feed"})
        for article in feed.articles:
            article_div = soup.new_tag("div", **{"class": "article"})

            # Title
            title_div = soup.new_tag("div", **{"class": "article-title"})
            title_link = soup.new_tag("a", href=article.link, target="_blank", rel="noopener noreferrer")
            title_link.string = article.title
            title_div.append(title_link)
            article_div.append(title_div)

            # Metadata
            meta_div = soup.new_tag("div", **{"class": "article-meta"})
            meta_div.string = f"Publié: {article.published} | Source: {article.source_feed}"
            article_div.append(meta_div)

            # Summary
            if article.summary:
                summary_p = soup.new_tag("p", **{"class": "article-summary"})
                summary_p.string = article.summary
                article_div.append(summary_p)

            feed_div.append(article_div)
        container.append(feed_div)

    # Footer
    footer = soup.new_tag("div", **{"class": "footer"})
    footer.string = f"© {datetime.now().year} Epic News Inc. - Total Feeds: {report_model.total_feeds}, Total Articles: {report_model.total_articles}"
    container.append(footer)

    try:
        html_content = str(soup.prettify())
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"✅ RSS Weekly HTML report saved to {html_file}")
        return html_content
    except OSError as e:
        logger.error(f"❌ Failed to write HTML report to {html_file}: {e}")
        return ""
