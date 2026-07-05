"""Tests for the SAINT renderer via the public TemplateManager.render_report() path.

Covers `src/epic_news/utils/html/template_renderers/saint_renderer.py`:
- header (name + optional title/epithet subtitle)
- biography (biography/life_story/summary fallbacks)
- feast details (feast_day/feast_date/celebration_date, birth/death year,
  patronage/patron_of as list or string, symbols/attributes as list or string)
- miracles (string or list)
- swiss connection
- spiritual significance (spiritual_significance/significance/teachings/legacy,
  string or list)
- prayer/reflection (prayer_reflection/prayer/reflection fallbacks)
- sources (list, including empty/invalid edge cases)
"""

from bs4 import BeautifulSoup

from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.utils.html.template_manager import TemplateManager


def _render(data: dict) -> str:
    return TemplateManager().render_report("SAINT", data)


def test_full_data_from_pydantic_model():
    """Render the real SaintData model (as produced by SaintDailyCrew) end-to-end."""
    saint = SaintData(
        saint_name="Saint Nicolas de Flüe",
        feast_date="21 mars",
        biography=(
            "Nicolas de Flue, egalement connu sous le nom de Frere Nicolas, est un ermite "
            "et mystique suisse ne en 1417 a Flueli, dans le canton d'Obwald."
        ),
        significance=(
            "Il est venere comme le saint patron de la Suisse et un symbole de paix et de "
            "mediation nationale."
        ),
        miracles=(
            "Il aurait vecu vingt ans sans autre nourriture que l'Eucharistie, un jeune "
            "prolonge considere comme miraculeux."
        ),
        swiss_connection=(
            "Il est le saint patron de la Suisse, ayant contribue a la paix du pays lors "
            "de la Diete de Stans en 1481."
        ),
        prayer_reflection=(
            "Seigneur, prends tout ce qui m'eloigne de Toi. "
            "Seigneur, donne-moi tout ce qui me rapproche de Toi."
        ),
        sources=["Vatican News", "Diocese de Bale"],
        birth_year="1417",
        death_year="1487",
        patron_of="Suisse, paix, mediation",
    )

    html = _render(saint.model_dump())

    # Structure
    assert "<!DOCTYPE html>" in html
    assert 'class="saint-report"' in html
    assert 'class="saint-header"' in html
    assert 'class="saint-biography"' in html
    assert 'class="feast-details"' in html
    assert 'class="miracles"' in html
    assert 'class="swiss-connection"' in html
    assert 'class="spiritual-significance"' in html
    assert 'class="prayer-reflection"' in html
    assert 'class="sources"' in html

    # The model has no "name"/"title"/"epithet" fields, so the header falls back
    # to the default name and no subtitle is rendered.
    assert "✨ Saint" in html
    assert 'class="saint-title"' not in html

    # Content fed in
    assert "Nicolas de Flue" in html
    assert "21 mars" in html
    assert "1417" in html
    assert "1487" in html
    assert "Suisse, paix, mediation" in html
    assert "Eucharistie" in html
    assert "Diete de Stans" in html
    assert "Seigneur, donne-moi tout ce qui me rapproche de Toi." in html
    assert "Vatican News" in html
    assert "Diocese de Bale" in html


def test_full_data_plain_dict_with_lists():
    """Every optional section populated via list-typed fields and primary field names."""
    data = {
        "name": "Sainte Claire d'Assise",
        "title": "Fondatrice des Clarisses",
        "feast_day": "11 aout",
        "patronage": ["television", "brodeuses", "blanchisseuses"],
        "symbols": ["ciboire", "lampe", "habit religieux"],
        "miracles": [
            "Guerison miraculeuse d'un frere malade",
            "Vision de la messe de Noel projetee sur le mur de sa cellule",
        ],
        "spiritual_significance": [
            "Elle incarne l'ideal de pauvrete evangelique.",
            "Elle inspire le dialogue interreligieux moderne.",
        ],
        "swiss_connection": "Un monastere de Clarisses existe a Fribourg en Suisse.",
        "prayer": "Louee sois-tu, Seigneur, pour notre soeur Claire, lumiere de simplicite.",
        "sources": ["Franciscans.org", "Vatican.va", "Diocese de Fribourg"],
    }

    html = _render(data)
    soup = BeautifulSoup(html, "html.parser")

    assert "<!DOCTYPE html>" in html
    assert "Sainte Claire d'Assise" in html
    assert 'class="saint-title"' in html
    assert "Fondatrice des Clarisses" in html
    assert "11 aout" in html

    # Patronage rendered as a comma-joined list
    assert "television, brodeuses, blanchisseuses" in html
    # Symbols rendered as a comma-joined list
    assert "ciboire, lampe, habit religieux" in html

    miracles_div = soup.find("div", class_="miracles")
    assert miracles_div is not None
    miracle_items = [li.get_text() for li in miracles_div.find_all("li")]
    assert "Guerison miraculeuse d'un frere malade" in miracle_items
    assert "Vision de la messe de Noel projetee sur le mur de sa cellule" in miracle_items

    significance_div = soup.find("div", class_="spiritual-significance")
    assert significance_div is not None
    significance_items = [li.get_text() for li in significance_div.find_all("li")]
    assert "Elle incarne l'ideal de pauvrete evangelique." in significance_items
    assert "Elle inspire le dialogue interreligieux moderne." in significance_items

    assert "Un monastere de Clarisses existe a Fribourg en Suisse." in html
    assert "Louee sois-tu, Seigneur, pour notre soeur Claire, lumiere de simplicite." in html

    sources_div = soup.find("div", class_="sources")
    assert sources_div is not None
    source_items = [li.get_text() for li in sources_div.find_all("li")]
    assert source_items == ["Franciscans.org", "Vatican.va", "Diocese de Fribourg"]


def test_alternate_field_names_and_string_values():
    """Exercise the secondary/tertiary fallback keys and string (non-list) variants."""
    data = {
        "name": "Saint Martin de Tours",
        "epithet": "L'Apotre des Gaules",  # no "title" key present
        "life_story": (
            "Ne en Hongrie, il devint eveque de Tours et est celebre pour avoir partage "
            "son manteau avec un mendiant."
        ),  # no "biography" key present
        "celebration_date": "11 novembre",  # no "feast_day"/"feast_date" key present
        "patron_of": "soldats, cavaliers, mendiants",  # string, not a list
        "attributes": "manteau partage en deux",  # string, not a list; "attributes" not "symbols"
        "teachings": (
            "Son geste de partage symbolise la charite chretienne et la solidarite envers les plus demunis."
        ),  # tertiary fallback key for significance
        "reflection": (
            "Que ce jour nous rappelle l'importance du partage envers ceux qui souffrent."
        ),  # tertiary fallback key for prayer
        "sources": ["Nominis - Saints du jour"],
    }

    html = _render(data)

    assert "Saint Martin de Tours" in html
    assert 'class="saint-title"' in html
    assert "L'Apotre des Gaules" in html

    assert 'class="saint-biography"' in html
    assert "eveque de Tours" in html

    assert 'class="feast-details"' in html
    assert "11 novembre" in html
    assert "soldats, cavaliers, mendiants" in html
    assert "manteau partage en deux" in html

    assert 'class="spiritual-significance"' in html
    assert "charite chretienne" in html

    assert 'class="prayer-reflection"' in html
    assert "importance du partage" in html

    assert 'class="sources"' in html
    assert "Nominis - Saints du jour" in html


def test_minimal_empty_data_no_crash():
    """Rendering with no fields at all must not crash and yields minimal, valid HTML."""
    html = _render({})

    assert "<!DOCTYPE html>" in html
    assert 'class="saint-report"' in html
    assert 'class="saint-header"' in html
    # Default header name fallback
    assert "✨ Saint" in html

    # None of the optional sections should be present
    for marker in (
        'class="saint-title"',
        'class="saint-biography"',
        'class="feast-details"',
        'class="miracles"',
        'class="swiss-connection"',
        'class="spiritual-significance"',
        'class="prayer-reflection"',
        'class="sources"',
    ):
        assert marker not in html


def test_sources_and_miracles_type_edge_cases():
    """Cover the defensive branches: empty/non-list sources, non-str/non-list miracles."""
    # Empty list -> "not sources" short-circuits, section omitted entirely.
    html_empty_sources = _render({"name": "Saint Test", "miracles": "x", "sources": []})
    assert 'class="sources"' not in html_empty_sources

    # Truthy but non-list sources -> "not isinstance(sources, list)" branch, omitted.
    html_bad_sources = _render({"name": "Saint Test", "miracles": "x", "sources": "not-a-list"})
    assert 'class="sources"' not in html_bad_sources

    # Miracles present but neither str nor list -> header renders, no <ul>/<p> content added.
    html = _render({"name": "Saint Test", "miracles": 42})
    soup = BeautifulSoup(html, "html.parser")
    miracles_div = soup.find("div", class_="miracles")
    assert miracles_div is not None
    assert miracles_div.find("ul") is None
    assert miracles_div.find("p") is None
    assert miracles_div.find("h3").get_text() == "✨ Miracles"
