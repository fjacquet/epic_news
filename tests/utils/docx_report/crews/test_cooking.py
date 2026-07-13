import zipfile

from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils.docx_report.crews.cooking import assemble_cooking_docx


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

    Needed because the Informations table has a row labelled "Préparation"
    (per spec) that precedes the actual "Préparation" *heading* in the XML —
    a naive `txt.index(h)` for every heading would match that row instead.
    """
    indices = []
    pos = 0
    for h in headings:
        pos = txt.index(h, pos)
        indices.append(pos)
        pos += len(h)
    return indices


def _build_model(**overrides) -> PaprikaRecipe:
    defaults = {
        "name": "Crêpes",
        "servings": "4",
        "prep_time": "15 min",
        "cook_time": None,
        "difficulty": "Facile",
        "categories": ["Dessert", "Rapide"],
        "notes": "Servir tiède.",
        "ingredients": "200 g de farine\n3 œufs\n1 pincée de sel",
        "directions": "Mélanger la farine.\nAjouter les œufs.\nCuire 20 min.",
    }
    defaults.update(overrides)
    return PaprikaRecipe(**defaults)


def test_cooking_docx_with_notes(tmp_path):
    model = _build_model()
    llm = _StubLLM()
    out = assemble_cooking_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "cooking.docx"), llm)
    txt = _text(out)

    # Ingredients survive verbatim, line-per-item (not char-per-line)
    assert "200 g de farine" in txt
    assert "3 œufs" in txt
    assert "1 pincée de sel" in txt

    # Directions survive verbatim, line-per-step
    assert "Mélanger la farine." in txt
    assert "Ajouter les œufs." in txt
    assert "Cuire 20 min." in txt

    # None-guarded: cook_time is None -> must render as em-dash, never literal "None"
    assert "None" not in txt
    assert "—" in txt

    # Only Notes is narrated (LLM-called); everything else is deterministic
    assert llm.calls == 1

    headings = ["Informations", "Ingrédients", "Préparation", "Notes"]
    indices = _sequential_indices(txt, headings)
    assert indices == sorted(indices)


def test_cooking_docx_without_notes(tmp_path):
    model = _build_model(notes=None)
    llm = _StubLLM()
    out = assemble_cooking_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "cooking.docx"), llm)
    txt = _text(out)

    # No notes -> no LLM call at all, all sections deterministic
    assert llm.calls == 0

    # Notes section must be entirely absent
    assert "Notes" not in txt

    headings = ["Informations", "Ingrédients", "Préparation"]
    indices = _sequential_indices(txt, headings)
    assert indices == sorted(indices)
