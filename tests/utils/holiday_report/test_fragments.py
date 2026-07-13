from epic_news.utils.docx_report import generate_fragment


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
    md = generate_fragment(
        "Restauration", "Liste les restaurants.", "recherche", OkLLM(), system="Tu es un rédacteur de voyage."
    )
    assert "Markdown" in md


def test_fragment_returns_placeholder_on_failure():
    md = generate_fragment(
        "Budget", "Détaille le budget.", "recherche", FailLLM(), system="Tu es un rédacteur de voyage."
    )
    assert "indisponible" in md.lower()


def test_fragment_returns_placeholder_on_empty():
    md = generate_fragment(
        "Budget", "Détaille le budget.", "recherche", EmptyLLM(), system="Tu es un rédacteur de voyage."
    )
    assert "indisponible" in md.lower()
