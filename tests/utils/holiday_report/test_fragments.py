from epic_news.utils.holiday_report.fragments import generate_fragment


class OkLLM:
    def call(self, messages):
        return "Contenu **riche** en Markdown."


class FailLLM:
    def call(self, messages):
        raise TimeoutError("provider timed out")


class EmptyLLM:
    def call(self, messages):
        return "   "


def test_fragment_returns_markdown_on_success():
    md = generate_fragment("Restauration", "Liste les restaurants.", "recherche", OkLLM())
    assert "Markdown" in md


def test_fragment_returns_placeholder_on_failure():
    md = generate_fragment("Budget", "Détaille le budget.", "recherche", FailLLM())
    assert "indisponible" in md.lower()


def test_fragment_returns_placeholder_on_empty():
    md = generate_fragment("Budget", "Détaille le budget.", "recherche", EmptyLLM())
    assert "indisponible" in md.lower()
