"""Deterministic Markdown-table rendering for data-heavy DOCX sections (exact values preserved)."""


def md_table(rows: list[dict], columns: list[tuple[str, str]]) -> str:
    """Render rows as a GitHub-flavored Markdown table. `columns` = [(header, key), ...].
    Cells are stringified and pipe/newline-escaped so exact values survive verbatim."""
    if not rows:
        return "_Aucune donnée._"

    def esc(v: object) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ").strip()

    header = "| " + " | ".join(h for h, _ in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = "\n".join("| " + " | ".join(esc(r.get(k, "")) for _, k in columns) + " |" for r in rows)
    return f"{header}\n{sep}\n{body}"
