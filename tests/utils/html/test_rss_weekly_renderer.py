"""Unit tests for RssWeeklyRenderer, exercised via TemplateManager.render_report().

These tests target the real rendering logic in
``src/epic_news/utils/html/template_renderers/rss_weekly_renderer.py``:
feed digests, category grouping, flat article lists, article cards (canonical
and legacy key fallbacks), sources, and empty-state handling.
"""

from epic_news.models.crews.rss_weekly_report import ArticleSummary, FeedDigest, RssWeeklyReport
from epic_news.utils.html.template_manager import TemplateManager


def _render(data: dict) -> str:
    return TemplateManager().render_report("RSS_WEEKLY", data)


def test_full_report_multiple_feeds_and_articles():
    """Canonical RssWeeklyReport shape: multiple feeds, each with multiple articles."""
    report = RssWeeklyReport(
        title="Digest Hebdomadaire Tech",
        summary="Cette semaine, forte actualite autour de l'IA generative.",
        feeds=[
            FeedDigest(
                feed_url="https://techradar.example.com/rss",
                feed_name="Tech Radar Weekly",
                articles=[
                    ArticleSummary(
                        title="L'IA generative bouscule le developpement logiciel",
                        link="https://techradar.example.com/articles/ai-dev",
                        published="2026-06-30",
                        summary="Un tour d'horizon des outils d'IA pour developpeurs.",
                        source_feed="https://techradar.example.com/rss",
                    ),
                    ArticleSummary(
                        title="Nouveau record de performance pour les puces ARM",
                        link="https://techradar.example.com/articles/arm-record",
                        published="2026-07-01",
                        summary="Les benchmarks montrent un gain de 30%.",
                        source_feed="https://techradar.example.com/rss",
                    ),
                ],
            ),
            FeedDigest(
                feed_url="https://sciencedaily.example.com/rss",
                feed_name="Science Daily Digest",
                articles=[
                    ArticleSummary(
                        title="Decouverte d'une exoplanete prometteuse",
                        link="https://sciencedaily.example.com/articles/exoplanet",
                        published="2026-07-02",
                        summary="Une planete potentiellement habitable a ete identifiee.",
                        source_feed="https://sciencedaily.example.com/rss",
                    ),
                ],
            ),
        ],
    )

    html = _render(report.model_dump())

    # Structural markers
    assert "<!DOCTYPE html>" in html
    assert 'class="feed-digest"' in html
    assert 'class="article-summary"' in html
    assert 'class="articles-list"' in html

    # Header
    assert "📰 Digest Hebdomadaire Tech" in html
    assert "Cette semaine, forte actualite autour de l'IA generative." in html

    # Feed names (with 📡 prefix as emitted by the renderer)
    assert "📡 Tech Radar Weekly" in html
    assert "📡 Science Daily Digest" in html

    # Feed URLs rendered as links
    assert 'href="https://techradar.example.com/rss"' in html
    assert 'href="https://sciencedaily.example.com/rss"' in html

    # Article counts per feed
    assert "2 article(s)" in html
    assert "1 article(s)" in html

    # Article titles (exact content fed in)
    assert "L'IA generative bouscule le developpement logiciel" in html
    assert "Nouveau record de performance pour les puces ARM" in html
    assert "Decouverte d'une exoplanete prometteuse" in html

    # Article links
    assert 'href="https://techradar.example.com/articles/ai-dev"' in html
    assert 'href="https://sciencedaily.example.com/articles/exoplanet"' in html

    # Published dates
    assert "📅 2026-06-30" in html
    assert "📅 2026-07-02" in html

    # Source feed rendered on the article card
    assert "📡 https://techradar.example.com/rss" in html

    # Article summaries (parsed via BeautifulSoup fragment)
    assert "Un tour d'horizon des outils d'IA pour developpeurs." in html
    assert "Une planete potentiellement habitable a ete identifiee." in html


def test_empty_minimal_data_does_not_crash():
    """No feeds at all: renderer must not crash and must still produce valid HTML."""
    report = RssWeeklyReport()  # defaults: no feeds, no summary, default title

    html = _render(report.model_dump())

    assert "<!DOCTYPE html>" in html
    # Default title from the model, with renderer's emoji prefix
    assert "📰 Résumé Hebdomadaire des Flux RSS" in html
    # No feed/category/article sections should be present
    assert 'class="feed-digest"' not in html
    assert 'class="rss-category"' not in html
    assert 'class="rss-articles"' not in html
    # No summary section since summary is None
    assert 'class="rss-summary"' not in html
    # Sanity: still a substantial HTML document
    assert len(html) > 200


def test_feed_without_url_falls_back_to_unknown_name_and_skips_url_paragraph():
    """feed_url='' and feed_name=None => 'Unknown feed' fallback, no <p class="feed-url">."""
    data = {
        "title": "Flux sans nom",
        "feeds": [
            {
                "feed_url": "",
                "feed_name": None,
                "articles": [],
            }
        ],
    }

    html = _render(data)

    assert "📡 Unknown feed" in html
    assert 'class="feed-url"' not in html
    # Zero articles still renders the count line
    assert "0 article(s)" in html


def test_feed_name_falls_back_to_feed_url_when_name_missing():
    """feed_name absent but feed_url present => feed_name falls back to feed_url."""
    data = {
        "feeds": [
            {
                "feed_url": "https://onlyurl.example.com/rss",
                "articles": [],
            }
        ],
    }

    html = _render(data)

    assert "📡 https://onlyurl.example.com/rss" in html
    assert 'class="feed-url"' in html


def test_legacy_flat_articles_shape_with_legacy_article_keys():
    """Legacy top-level 'articles' shape (no 'feeds'/'categories'), legacy article keys."""
    data = {
        "title": "Vieux Format",
        "articles": [
            {
                "title": "Article avec cles historiques",
                "url": "https://legacy.example.com/a1",
                "date": "2026-06-15",
                "source": "Legacy Source",
                "description": "Une description historique.",
            },
            {
                "title": "Article avec contenu au lieu de summary",
                "url": "https://legacy.example.com/a2",
                "content": "Contenu detaille de l'article legacy.",
            },
        ],
    }

    html = _render(data)

    assert 'class="rss-articles"' in html
    assert "📑 Articles" in html
    assert 'class="articles-grid"' in html

    # Legacy 'url' used as href
    assert 'href="https://legacy.example.com/a1"' in html
    assert 'href="https://legacy.example.com/a2"' in html

    # Legacy 'date' -> published
    assert "📅 2026-06-15" in html

    # Legacy 'source' -> source_feed display
    assert "📡 Legacy Source" in html

    # 'description' rendered
    assert "Une description historique." in html

    # 'content' falls back into the summary block when 'summary' is absent
    assert "Contenu detaille de l'article legacy." in html


def test_categories_shape_groups_articles_by_category():
    """Top-level 'categories' dict groups articles into per-category sections."""
    data = {
        "categories": {
            "Technologie": [
                {"title": "Article Tech 1", "link": "https://cat.example.com/t1"},
            ],
            "Science": [
                {"title": "Article Science 1", "link": "https://cat.example.com/s1"},
                {"title": "Article Science 2", "link": "https://cat.example.com/s2"},
            ],
        }
    }

    html = _render(data)

    assert 'class="rss-category"' in html
    assert 'class="category-title"' in html
    assert 'class="category-articles"' in html
    assert "Technologie" in html
    assert "Science" in html
    assert "Article Tech 1" in html
    assert "Article Science 1" in html
    assert "Article Science 2" in html

    # 'categories' shape takes precedence over the flat-articles fallback:
    # no rss-articles section should be emitted.
    assert 'class="rss-articles"' not in html


def test_sources_section_with_and_without_urls():
    """Sources with a URL render as links; name-only sources render as plain text;
    sources without a name are skipped entirely."""
    data = {
        "feeds": [],
        "sources": [
            {"name": "Source Avec Lien", "url": "https://source-a.example.com"},
            {"name": "Source Sans Lien"},
            {"url": "https://orphan-url.example.com"},  # no name => skipped
        ],
    }

    html = _render(data)

    assert "📚 Sources" in html
    assert 'class="sources-list"' in html

    # Source with URL -> anchor tag
    assert 'href="https://source-a.example.com"' in html
    assert "Source Avec Lien" in html

    # Source with name only -> no anchor for it, but name text present
    assert "Source Sans Lien" in html

    # Source without a name is skipped: its URL should not appear anywhere
    assert "orphan-url.example.com" not in html


def test_article_card_without_link_renders_plain_title_and_skips_optional_fields():
    """Article with only a title (no link/url, no published, no source, no
    description/summary) renders a bare <h4> with no anchor and no extra paragraphs."""
    data = {
        "articles": [
            {"title": "Titre Seul Sans Rien D'Autre"},
        ],
    }

    html = _render(data)

    # Bare title, no nested <a> tag
    assert "<h4>Titre Seul Sans Rien D'Autre</h4>" in html
    assert 'class="published-date"' not in html
    assert 'class="article-meta"' not in html
    assert 'class="article-description"' not in html
    assert 'class="summary"' not in html


def test_header_date_rendered_when_present():
    """Top-level 'date' key (legacy/manual shape) renders the optional date paragraph."""
    data = {
        "title": "Rapport Date",
        "date": "Semaine du 30 juin 2026",
        "feeds": [],
    }

    html = _render(data)

    assert 'class="rss-date"' in html
    assert "Semaine du 30 juin 2026" in html
