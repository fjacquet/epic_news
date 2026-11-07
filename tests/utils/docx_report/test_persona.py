from epic_news.utils.docx_report import persona


def test_persona_uses_request_language_extra_rule_and_request():
    system = persona(
        "un chef cuisinier",
        {"language": "English", "user_preferences_and_constraints": "sans gluten, 6 personnes"},
        extra="Ne modifie JAMAIS les quantités.",
    )
    assert system.startswith("Tu es un chef cuisinier.")
    assert "en English" in system
    assert "Ne modifie JAMAIS les quantités." in system
    assert "La demande de l'utilisateur prime" in system
    assert "sans gluten, 6 personnes" in system


def test_persona_defaults_to_french_and_omits_empty_request():
    system = persona("un analyste", {})
    assert "en French" in system
    assert "demande de l'utilisateur" not in system
