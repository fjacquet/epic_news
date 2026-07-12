# Holiday report: fragment generation → Pandoc DOCX

**Date:** 2026-07-12
**Status:** Design (approved in brainstorming, pending spec review)
**Scope:** `holiday_planner` crew + its slice of `ReceptionFlow`. No other crew changes.

## Problem

The holiday report is produced by a single LLM call: the `content_formatter` agent runs
`format_and_translate_guide`, whose `expected_output` demands *"a single JSON object …
exhaustive … detail ALL information"* (intro + full day-by-day itinerary + accommodations +
dining + budget + practical info + sources + media), validated against `HolidayPlannerReport`
via `output_pydantic`.

On a real 15-day, multi-stop request this one generation:

- **Times out / aborts.** Observed `litellm.Timeout: The operation was aborted` after ~1800 s
  (mistral-large-2407), and `provider_unavailable` 502 "Stream ended before a terminal response
  event" (gpt-5.6-terra) — the long stream is dropped mid-response.
- **Loses everything on truncation.** A cut stream yields invalid JSON
  (`Invalid JSON: EOF while parsing … column 10639`) → `output_pydantic` validation fails → the
  entire ~30 min run is discarded. All-or-nothing.

The generation *size* is the root cause, not the HTML rendering. A deterministic Python
renderer cannot help because the oversized artefact is the **LLM content generation**, not the
formatting step.

## Goal / success criteria

- A **rich, complete** holiday guide that **never hits the per-call generation limit**,
  regardless of trip length.
- **Graceful degradation:** one failed sub-generation never discards the whole report.
- Delivered as an editable **DOCX** attached to the existing email step.
- **Cross-platform** dev (macOS) and Docker (Linux) with no fragile system dependencies
  (explicitly avoiding WeasyPrint, headless browsers, and LaTeX).
- Contained to `holiday_planner`; other crews untouched.

## Approach (decided in brainstorming)

Split the one giant generation into **bounded Markdown fragments**, assemble them with
**Pandoc → DOCX**. Markdown (not strict JSON) is the generation format so a truncated fragment
stays readable and never fails schema validation.

Decisions made:

- **Split dimension:** hybrid — one fragment per section, plus **one fragment per itinerary
  day** (the only part that scales with trip length).
- **Artefact:** DOCX only, via `pypandoc-binary` (bundles the pandoc binary in the pip wheel;
  no apt/brew/browser/system libs). PDF is out of scope; the user exports from DOCX if needed.
- **MkDocs is not used** — Pandoc both concatenates the fragments and converts.

## Architecture

```
research crew (unchanged)         fragment layer (new, flow-driven)         assembly (new)
──────────────────────────        ─────────────────────────────────        ────────────────
travel_researcher        ─┐       intro fragment        (1 LLM call)   ─┐
accommodation_specialist  ├─ raw  accommodations fragment (1 call)      │   pandoc via
itinerary_architect       ├─ ───► dining fragment        (1 call)       ├─► pypandoc ──► guide.docx ──► email
budget_manager           ─┘ research  budget fragment    (1 call)       │   (--toc,
                                   practical fragment     (1 call)       │    reference.docx)
                                   itinerary skeleton     (1 call)      │
                                   day-01 … day-NN        (N calls)    ─┘
```

The 4 research agents keep gathering info exactly as today. Only the **final assembly** changes:
the single `content_formatter` mega-call is replaced by the fragment layer + Pandoc.

## Components (isolated units)

### 1. `HolidayFragmentGenerator`
- **Does:** given (research context, fragment spec) → returns a Markdown string for that one
  fragment. One bounded LLM call. On failure (timeout / provider error / empty), returns a
  placeholder Markdown block (`> ⚠️ Section indisponible (…)`) instead of raising.
- **Uses:** the project LLM (`LLMConfig.get_openrouter_llm()`), the relevant slice of research
  output, and a small shared trip summary for coherence. No `output_pydantic` — raw Markdown.
- **Testable** with a mocked LLM: returns MD on success, placeholder on failure.

### 2. Fragment set
Section fragments (one call each): `intro`, `accommodations`, `dining`, `budget`, `practical`
(packing checklist, safety, emergency contacts, useful phrases).

Itinerary fragments (bounded regardless of trip length):
- An **itinerary skeleton** call returns a **small structured day list** — one entry per day
  (`date`, `label`, `stops`). Structured (not free MD) so the per-day loop has a deterministic
  count and stable dates; the list is short, so this call stays safely under the limit even for
  long trips.
- Then **one fragment per day**, each generated from that day's skeleton entry + relevant
  research. Coherent (each sees the skeleton) and individually tiny.

### 3. `DocxReportBuilder`
- **Does:** given an ordered `{filename: markdown}` map + metadata (title, author, date) →
  writes the `.md` files to a temp dir, invokes Pandoc (`pypandoc.convert_file`/`convert_text`
  with `--toc`, `--reference-doc=<style.docx>`), returns the DOCX path.
- **No LLM**, fully deterministic. **Testable** with fixture fragments → produces a valid DOCX.
- A committed `reference.docx` (or generated default) carries fonts/heading styles/branding.

### 4. Flow glue in `generate_holiday_plan`
Orchestrates: kick off research crew → generate section fragments (can be concurrent) →
skeleton → per-day fragments (loop) → `DocxReportBuilder` → set the email attachment to the DOCX.

## Data flow

1. Research crew runs (4 tasks) → raw research outputs (kept as today).
2. Flow builds a compact **trip summary** (origin, dates, stops, party, prefs) from state — this
   is the small shared context every fragment call receives, keeping each prompt bounded.
3. Section fragments generated (each: trip summary + its research slice → Markdown).
4. Itinerary skeleton generated → day list.
5. Per-day fragments generated in a loop over the skeleton.
6. `DocxReportBuilder` orders fragments (intro → itinerary days → accommodations → dining →
   budget → practical → sources) and runs Pandoc → `output/holiday/guide.docx`.
7. `send_email` attaches `guide.docx`.

## Error handling (the robustness win)

- Every fragment call is independent and wrapped: failure → placeholder block, never an
  exception. The report **always assembles**.
- Per-fragment retry is cheap and safe (one small call), unlike replaying the whole crew.
- If Pandoc itself fails, fall back to a concatenated-Markdown `.md` attachment so the user still
  receives content, and log the failure via the `kickoff()` error path already added.
- `email_sent` continues to reflect only an API-confirmed delivery.

## Dependencies

- Add **`pypandoc-binary`** (`uv add pypandoc-binary`). The wheel bundles the pandoc binary per
  platform, so it must resolve for **both** macOS (dev) and Linux (Docker) in `uv.lock`
  (multi-platform lock). Verify the Docker image gets the Linux wheel; no apt packages needed.
- A `reference.docx` style asset committed under the holiday crew (or `templates/`).

## Retired (holiday only)

- `content_formatter` agent, `format_and_translate_guide` task.
- `HolidayPlannerReport` `output_pydantic` on the final task (the research tasks keep their
  outputs; only the final structured mega-output goes away).
- The holiday HTML renderer path for this crew's report (email now carries the DOCX).

## Testing

- `DocxReportBuilder`: fixture fragments → asserts a valid, non-empty DOCX with expected
  headings/TOC. No network, no LLM.
- `HolidayFragmentGenerator`: mocked LLM → returns Markdown on success; returns the placeholder
  block on a raised error / empty completion.
- Flow: mocked research crew + mocked generator → asserts fragment ordering, per-day loop length
  matches the skeleton, and the email attachment is the DOCX path.

## Out of scope / YAGNI

- No PDF pipeline (DOCX only; user exports if needed).
- No MkDocs, no browser, no LaTeX/WeasyPrint.
- No generalisation to other crews yet — revisit only if the holiday result is good.
- Media/images embedding is best-effort (links in a sources fragment); not a blocker.

## To validate during planning

- Exact fragment prompts and the research-output → fragment-slice mapping.
- Whether the itinerary skeleton is tiny structured output or a plain MD list.
- `reference.docx` styling and how headings/TOC render.
- `pypandoc-binary` multi-platform resolution in `uv.lock` for the Docker build.
