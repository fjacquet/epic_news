import json
import zipfile

from epic_news.models.crews.rss_weekly_report import ArticleSummary, FeedDigest, RssWeeklyReport
from epic_news.utils.docx_report.crews.rss_weekly import assemble_rss_docx
from epic_news.utils.report_utils import load_rss_weekly_report


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def test_assemble_rss_docx(tmp_path):
    # RssWeeklyReport.model_post_init recomputes total_feeds as len(feeds) and
    # total_articles as the sum of each feed's (pre-reset) total_articles — so a
    # second feed (with no real articles but an explicit total_articles=4) is
    # needed to genuinely land on "2 flux / 5 articles" after that recalculation.
    model = RssWeeklyReport(
        title="Veille-Hebdo",
        summary="Résumé veille.",
        total_feeds=2,
        total_articles=5,
        feeds=[
            FeedDigest(
                feed_url="https://f.example/rss",
                feed_name="Flux-Tech",
                articles=[
                    ArticleSummary(
                        title="Article-Titre",
                        link="https://a.example/1",
                        published="2026-07-13",
                        summary="Résumé-Article",
                        source_feed="https://f.example/rss",
                    )
                ],
                total_articles=1,
            ),
            FeedDigest(
                feed_url="https://g.example/rss",
                feed_name="Flux-Bis",
                articles=[],
                total_articles=4,
            ),
        ],
    )
    llm = _StubLLM()
    out = assemble_rss_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r.docx"), llm)
    txt = _text(out)
    assert "Article-Titre" in txt  # deterministic article title verbatim
    assert "Résumé-Article" in txt  # deterministic article summary verbatim
    assert "Flux-Tech" in txt  # feed heading
    assert "2 flux · 5 articles" in txt  # deterministic Aperçu body
    # narrated: only Résumé is narrated (Aperçu + per-feed digests are deterministic bodies)
    assert llm.calls == 1
    # section headings appear in the expected order
    headings = ["Résumé", "Aperçu", "Flux-Tech"]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)


def test_load_rss_weekly_report_both_shapes(tmp_path):
    # RssWeeklyReport shape: used directly.
    direct_path = tmp_path / "direct.json"
    direct_path.write_text(
        json.dumps(
            {
                "title": "Veille-Directe",
                "feeds": [],
                "total_feeds": 0,
                "total_articles": 0,
                "summary": None,
            }
        ),
        encoding="utf-8",
    )
    direct_model = load_rss_weekly_report(str(direct_path))
    assert direct_model.title == "Veille-Directe"

    # RssFeeds shape: transformed via _transform_rss_feeds_to_report.
    feeds_path = tmp_path / "feeds.json"
    feeds_path.write_text(
        json.dumps({"rss_feeds": [{"feed_url": "u", "articles": []}]}),
        encoding="utf-8",
    )
    transformed_model = load_rss_weekly_report(str(feeds_path))
    assert isinstance(transformed_model, RssWeeklyReport)
