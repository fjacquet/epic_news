from docx import Document

from epic_news.models.crews.poem_report import PoemJSONOutput
from epic_news.utils.docx_report.crews import poem as poem_mod


def test_poem_docx_keeps_title_lines_and_stanzas(monkeypatch, tmp_path):
    captured = {}

    def fake_build(fragments, meta, output_path):
        captured.update(fragments=fragments, meta=meta)
        return output_path

    monkeypatch.setattr(poem_mod, "build_docx", fake_build)
    model = PoemJSONOutput(title="Automne", poem="Les feuilles tombent\nsur le lac\n\nle vent se tait")
    out = poem_mod.assemble_poem_docx(model, {}, "output/poem/poem.docx")

    assert out == "output/poem/poem.docx"
    assert captured["meta"]["title"] == "Automne"
    body = "\n".join(text for _, text in captured["fragments"])
    assert "Les feuilles tombent  \nsur le lac" in body and "le vent se tait" in body
    assert "\n\n" in body


def test_poem_docx_makes_no_llm_call(monkeypatch):
    monkeypatch.setattr(poem_mod, "build_docx", lambda fragments, meta, output_path: output_path)

    class NoLLM:
        def call(self, *_a, **_k):
            raise AssertionError("the poem must not be narrated")

    poem_mod.assemble_poem_docx(PoemJSONOutput(title="T", poem="x"), {}, "output/poem/p.docx", llm=NoLLM())


def test_poem_docx_real_build_keeps_each_line(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    model = PoemJSONOutput(title="Automne", poem="Les feuilles tombent\nsur le lac\n\nle vent se tait")
    out = poem_mod.assemble_poem_docx(model, {}, "output/poem/poem.docx")

    paragraphs = [p.text for p in Document(out).paragraphs]
    assert "Les feuilles tombent\nsur le lac" in paragraphs
    assert "le vent se tait" in paragraphs
