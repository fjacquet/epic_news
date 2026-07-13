import zipfile

from epic_news.models.crews.news_daily_report import NewsDailyReport, NewsItem
from epic_news.utils.docx_report.crews.news_daily import assemble_news_daily_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def _sequential_indices(txt: str, headings: list[str]) -> list[int]:
    """Find each heading in order, searching forward from the previous match.

    A forward scan keeps the order check robust against any incidental repeat
    of a heading string elsewhere in the document (e.g. "Suisse" recurring
    inside the earlier "Suisse Romande" heading).
    """
    indices = []
    pos = 0
    for h in headings:
        pos = txt.index(h, pos)
        indices.append(pos)
        pos += len(h)
    return indices


def test_news_daily_docx(tmp_path):
    model = NewsDailyReport(
        summary="Résumé du jour.",
        suisse_romande=[
            NewsItem.model_validate({"title": "Titre-Romandie", "source": "RTS", "link": "http://rts.ch"})
        ],
        methodology=None,
    )
    # NewsDailyReport's field_validators normalize any str/list[str] passed at
    # construction time into list[NewsItem] (or [] for a bare str) for these fields,
    # so the only way to exercise the genuine `str` / `list[str]` union members (as the
    # type annotations `list[NewsItem] | str` and `list[NewsItem] | list[str] | str`
    # allow) is direct attribute assignment post-construction, which bypasses
    # validation (validate_assignment=False).
    model.france = "Actualité française en bloc."
    model.economy = ["Éco-Item-Un", "Éco-Item-Deux"]
    # validate_methodology stringifies any dict passed at construction time
    # (v.get("description", str(v))), which would collapse this into the raw
    # Python-dict repr and silently defeat the assembler's `dict` branch. Assign
    # post-construction (same validator-bypass technique as above) to keep it a
    # real dict and genuinely exercise `_methodology_body`'s dict branch.
    model.methodology = {"sources": "42 flux"}
    llm = _StubLLM()
    out = assemble_news_daily_docx(
        model, {"current_date": "2026-07-13", "topic": "Actualités"}, str(tmp_path / "news.docx"), llm
    )
    txt = _text(out)

    for verbatim in [
        "Titre-Romandie",
        "RTS",
        "Actualité française en bloc.",
        "Éco-Item-Un",
        "Éco-Item-Deux",
        "42 flux",
    ]:
        assert verbatim in txt, f"missing verbatim content: {verbatim}"

    # Discriminate the assembler's dict branch (bold "- **key** : value" bullets)
    # from its str fallback: the dict key must render as a bullet label, and the
    # raw Python-dict repr must never leak into the document.
    assert "sources" in txt
    assert "{'sources'" not in txt

    assert "None" not in txt

    # only the Résumé narrates; every region + methodology is deterministic
    assert llm.calls == 1

    headings = [
        "Résumé",
        "Suisse Romande",
        "Suisse",
        "France",
        "Europe",
        "Monde",
        "Conflits",
        "Économie",
        "Méthodologie",
    ]
    indices = _sequential_indices(txt, headings)
    assert indices == sorted(indices)


def test_news_daily_docx_no_summary_no_methodology(tmp_path):
    model = NewsDailyReport(
        summary=None,
        suisse=[NewsItem.model_validate({"title": "Titre-Suisse", "source": "RTS"})],
        methodology=None,
    )
    llm = _StubLLM()
    out = assemble_news_daily_docx(
        model, {"current_date": "2026-07-13", "topic": "Actualités"}, str(tmp_path / "news2.docx"), llm
    )
    txt = _text(out)

    assert "Résumé" not in txt
    assert "Méthodologie" not in txt
    assert llm.calls == 0
