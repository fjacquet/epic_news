"""A narrated fragment must not repeat its section heading (build_docx already writes it)."""

import pytest

from epic_news.utils.docx_report.fragments import generate_fragment


class _LLM:
    def __init__(self, reply: str):
        self.reply = reply

    def call(self, _messages):
        return self.reply


@pytest.mark.parametrize(
    "reply",
    [
        "## Biographie\n\nNée en 1905, elle…",
        "# Biographie\n\nNée en 1905, elle…",
        "### **Biographie**\n\nNée en 1905, elle…",
        "## biographie :\n\nNée en 1905, elle…",
        "\n\n## Biographie\nNée en 1905, elle…",
    ],
)
def test_leading_heading_equal_to_the_section_is_dropped(reply):
    assert generate_fragment("Biographie", "Raconte", "ctx", _LLM(reply), "sys") == "Née en 1905, elle…"


def test_a_different_leading_heading_is_kept():
    reply = "## Les Prodiges de la Miséricorde\n\nTexte."
    assert generate_fragment("Miracles", "Raconte", "ctx", _LLM(reply), "sys") == reply


def test_a_repeated_heading_later_in_the_body_is_kept():
    reply = "Texte d'ouverture.\n\n## Biographie\n\nSuite."
    assert generate_fragment("Biographie", "Raconte", "ctx", _LLM(reply), "sys") == reply


def test_a_fragment_that_is_only_the_heading_degrades_to_the_placeholder():
    body = generate_fragment("Biographie", "Raconte", "ctx", _LLM("## Biographie"), "sys")
    assert "indisponible" in body
