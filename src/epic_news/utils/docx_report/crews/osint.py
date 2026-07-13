"""OSINT → DOCX: consolidate a cross-reference report plus 6 sub-reports.

Loads the raw JSON files that ``ReceptionFlow.generate_osint`` (``_run_osint_parallel``)
writes under ``output/osint/`` — the ``state`` attributes hold RAW crew output, not
parsed models, so we read the files directly as dicts. The cross-reference report
(``global_report.json``) supplies the narrated summary/confidence sections and the
deterministic findings/gaps; each present sub-report is rendered generically via a
recursive nested-bullet renderer (its fields are NOT hardcoded).
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un analyste OSINT. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Pas de HTML, pas de JSON, pas de préambule."
)

# Ordered (filename, French heading) for the six generic sub-reports.
_SUB_REPORTS: list[tuple[str, str]] = [
    ("company_profile.json", "Profil de l'entreprise"),
    ("tech_stack.json", "Pile technologique"),
    ("web_presence.json", "Présence web"),
    ("hr_intelligence.json", "Renseignement RH"),
    ("legal_analysis.json", "Analyse juridique"),
    ("geospatial_analysis.json", "Analyse géospatiale"),
]


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Aucune._"


def _scalar(v: Any) -> str:
    return "—" if v is None else str(v)


def _to_bullets(value: Any, indent: int = 0) -> str:
    """Render any JSON value (dict/list/scalar) as nested Markdown bullets.

    Total: never crashes on unexpected shapes. Empty dict/list → placeholder.
    """
    pad = "  " * indent
    if isinstance(value, dict):
        if not value:
            return "_Aucune donnée._"
        lines: list[str] = []
        for k, v in value.items():
            if isinstance(v, dict | list) and v:
                lines.append(f"{pad}- **{k}** :")
                lines.append(_to_bullets(v, indent + 1))
            else:
                lines.append(f"{pad}- **{k}** : {_scalar(v)}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return "_Aucune donnée._"
        lines = []
        for item in value:
            if isinstance(item, dict | list) and item:
                lines.append(f"{pad}-")
                lines.append(_to_bullets(item, indent + 1))
            else:
                lines.append(f"{pad}- {_scalar(item)}")
        return "\n".join(lines)
    return f"{pad}- {_scalar(value)}"


def _load_json(path: Path) -> dict | None:
    """Return the parsed JSON object, or None (with a warning) if missing/invalid.

    Never raises. A non-object top-level JSON value is treated as invalid.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("⚠️ OSINT report '{}' missing or invalid ({})", path, exc)
        return None
    if not isinstance(data, dict):
        logger.warning("⚠️ OSINT report '{}' is not a JSON object; skipping", path)
        return None
    return data


def assemble_osint_docx(
    inputs: dict, output_path: str, llm: Any = None, osint_dir: str = "output/osint"
) -> str:
    """Build the consolidated OSINT report as a DOCX from the raw JSON files.

    Narrated: executive summary + confidence assessment. Deterministic: detailed
    findings, each present sub-report (generic nested bullets), and information gaps.
    """
    llm = llm or LLMConfig.get_openrouter_llm()
    base = Path(osint_dir)
    cross = _load_json(base / "global_report.json") or {}

    sections: list[Section] = [
        Section(
            "Résumé exécutif",
            instruction="Reformule le résumé exécutif en prose fluide.",
            context=cross.get("executive_summary", ""),
        ),
        Section("Constats détaillés", body=_to_bullets(cross.get("detailed_findings", {}))),
    ]

    for filename, heading in _SUB_REPORTS:
        data = _load_json(base / filename)
        if data is not None:
            sections.append(Section(heading, body=_to_bullets(data)))

    sections.append(
        Section(
            "Évaluation de la confiance",
            instruction="Reformule l'évaluation de la confiance en prose claire.",
            context=cross.get("confidence_assessment", ""),
        )
    )
    sections.append(Section("Lacunes d'information", body=_bullets(cross.get("information_gaps", []))))

    meta = {
        "title": cross.get("target") or inputs.get("company") or inputs.get("topic") or "Rapport OSINT",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
