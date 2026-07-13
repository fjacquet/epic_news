"""RSS_WEEKLY → DOCX: narrated summary + deterministic overview and per-feed digests."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.rss_weekly_report import RssWeeklyReport
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un rédacteur de veille technologique. Rédige UNIQUEMENT la section demandée, "
    "en français, en Markdown propre. Pas de HTML, pas de JSON, pas de préambule."
)


def _feed_body(feed) -> str:
    if not feed.articles:
        return "_Aucun article._"
    return "\n".join(f"- **{a.title}** ({a.published}) : {a.summary} — {a.link}" for a in feed.articles)


def assemble_rss_docx(model: RssWeeklyReport, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the RSS_WEEKLY report as a DOCX: narrated summary + deterministic digests."""
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = []
    if model.summary:
        sections.append(
            Section("Résumé", instruction="Reformule le résumé en prose fluide.", context=model.summary)
        )
    sections.append(Section("Aperçu", body=f"{model.total_feeds} flux · {model.total_articles} articles."))
    for feed in model.feeds:
        sections.append(Section(feed.feed_name or feed.feed_url, body=_feed_body(feed)))
    meta = {
        "title": model.title or "Veille RSS",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
