"""System prompt shared by every narrated DOCX section."""

DEFAULT_LANGUAGE = "French"


def persona(role: str, inputs: dict, extra: str = "") -> str:
    """Build the narrator's system prompt: role, report language, the user's request first."""
    language = inputs.get("language") or DEFAULT_LANGUAGE
    request = inputs.get("user_preferences_and_constraints") or ""
    parts = [
        f"Tu es {role}. Rédige UNIQUEMENT la section demandée, en {language}.",
        extra,
        "Markdown propre : titres de niveau 2+, chaque élément de liste sur sa propre ligne, "
        "une ligne vide avant chaque liste. Pas de HTML, pas de JSON, pas de préambule.",
        f"La demande de l'utilisateur prime (ton, format, rubriques, contraintes) : {request}"
        if request
        else "",
    ]
    return " ".join(p for p in parts if p)
