import zipfile

from epic_news.models.crews.menu_designer_report import (
    DailyMeal,
    DailyMenu,
    DishInfo,
    DishType,
    MealType,
    WeeklyMenuPlan,
)
from epic_news.utils.docx_report.crews.menu import assemble_menu_docx


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
    of a heading string elsewhere in the document (e.g. inside a table cell).
    """
    indices = []
    pos = 0
    for h in headings:
        pos = txt.index(h, pos)
        indices.append(pos)
        pos += len(h)
    return indices


def _dish(name: str, dish_type: DishType, seasonal_ingredients: list[str]) -> DishInfo:
    return DishInfo(
        name=name,
        dish_type=dish_type,
        description=f"Description de {name}.",
        seasonal_ingredients=seasonal_ingredients,
        nutritional_highlights="Riche en fibres.",
    )


def _build_model(**overrides) -> WeeklyMenuPlan:
    lunch = DailyMeal(
        meal_type=MealType.DEJEUNER,
        starter=_dish("Salade-de-Saison", DishType.ENTREE, ["tomate"]),
        main_course=_dish("Tarte-aux-Poireaux", DishType.PLAT_PRINCIPAL, ["poireau"]),
        dessert=_dish("Compote-de-Pommes", DishType.DESSERT, ["pomme"]),
    )
    dinner = DailyMeal(
        meal_type=MealType.DINER,
        starter=_dish("Soupe-de-Legumes", DishType.ENTREE, ["carotte"]),
        main_course=_dish("Poulet-Roti", DishType.PLAT_PRINCIPAL, ["thym"]),
        dessert=None,
    )
    daily_menus = [DailyMenu(day="Lundi", date="2026-07-13", lunch=lunch, dinner=dinner)]
    defaults = {
        "week_start_date": "2026-07-13",
        "season": "Été",
        "daily_menus": daily_menus,
        "nutritional_balance": "Le menu est équilibré en macronutriments.",
        "gustative_coherence": "Les saveurs s'enchaînent harmonieusement.",
        "constraints_adaptation": "Adapté aux contraintes sans gluten.",
        "preferences_integration": "Intègre les préférences végétariennes.",
    }
    defaults.update(overrides)
    return WeeklyMenuPlan(**defaults)


def test_menu_docx_structure_and_fidelity(tmp_path):
    model = _build_model()
    llm = _StubLLM()
    out = assemble_menu_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "menu.docx"), llm)
    txt = _text(out)

    # Dish names survive verbatim (never rewritten by the LLM)
    assert "Tarte-aux-Poireaux" in txt

    # Seasonal ingredients are rendered
    assert "poireau" in txt

    # dessert=None on dinner must render as em-dash guard, never literal "None"
    assert "None" not in txt

    # Only the 3 narrated sections call the LLM (Aperçu + Menus quotidiens are deterministic)
    assert llm.calls == 3

    headings = [
        "Aperçu",
        "Menus quotidiens",
        "Équilibre nutritionnel",
        "Cohérence gustative",
        "Adaptations",
    ]
    indices = _sequential_indices(txt, headings)
    assert indices == sorted(indices)
