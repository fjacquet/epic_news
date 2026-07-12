# Prompt Enrichment in InformationExtractionCrew

**Date:** 2026-07-11
**Status:** Approved (design), pending implementation plan

## Problem

A real HOLIDAY_PLANNER run for a multi-stop road-trip request
(Montreux→Montpellier→Anglet→Poitiers→Bourges, French) produced no itinerary and
emailed the classifier's `decision.md` instead. Root cause: the request describes a
*route*, not a single destination, so `InformationExtractionCrew` dumped everything
into the free-text blob and left every structured travel field (`destination_location`,
`origin_location`, `event_or_trip_duration`, `traveler_details`) `None`.

A guard + fallback for that specific failure already shipped (see
`tests/flows/test_holiday_no_destination.py`). This spec addresses the upstream quality
lever: **messy, underspecified requests degrade extraction and, downstream, answer
quality across all crews.**

## Goal

Add a rephrase/enrich step that rewrites the raw user request into a clean, structured
brief. Downstream benefits are twofold:

1. Extraction runs on the clean brief, so structured fields fill reliably (a side
   effect that would have prevented the road-trip failure).
2. The enriched brief is passed to the downstream crew as `context`, giving it a
   rich, well-organized narrative to work from.

Non-goals: interactive user clarification loops; changing the `ExtractedInfo` schema;
altering classification or routing.

## Architecture

A new enrich task runs **first**, feeding a cleaned brief into the existing extraction
task. One crew, one kickoff, one flow step — `main.py::extract_info` keeps its shape.

```
feed_user_request
   ▼
extract_info  (single kickoff of the extended crew)
   ├─ enrich_request_task                  : raw request → enriched_brief (plain text)
   └─ comprehensive_information_extraction_task
        : ExtractedInfo, context=[enrich_request_task]   ← extracts from the clean brief
   ▼
classify → route → generate_<crew>
```

## Components

1. **New agent** `prompt_enricher_agent` (`config/agents.yaml`) — "Request Clarity
   Editor". No tools. Uses `LLMConfig.get_openrouter_llm()` and
   `LLMConfig.get_timeout("quick")`.
2. **New task** `enrich_request_task` (`config/tasks.yaml`) — outputs the enriched
   brief as plain text. Runs first (sequential process, listed before the extraction
   task).
3. **Existing task** `comprehensive_information_extraction_task` — gains
   `context=[self.enrich_request_task()]` so it extracts from the clean brief instead
   of the raw request.
4. **`ExtractedInfo`** (`src/epic_news/models/extracted_info.py`) — unchanged.
5. **`main.py::extract_info`** — after kickoff, read the enriched brief from
   `result.tasks_output[0].raw` and store `self.state.enriched_brief`. Falls back to
   the raw request when that output is empty/unusable.
6. **`ContentState`** (`src/epic_news/models/content_state.py`) — new field
   `enriched_brief: str | None = None`; `to_crew_inputs()` sets
   `context = enriched_brief or user_request` so downstream task templates that already
   reference `{context}` receive the rich narrative.

## Data Flow

```
raw user_request
   │
   ▼  enrich_request_task (LLM: reorganize + clarify, never invent)
enriched_brief ──────────────┬──────────────────────────────┐
   │                         │                               │
   ▼ context=[enrich]        ▼ state.enriched_brief          │
extract_task            (stored on ContentState)             │
   │                         │                               │
   ▼                         ▼ to_crew_inputs()              │
ExtractedInfo           context = enriched_brief ────────────┘
   │                         │
   ▼ field mapping           ▼
destination/duration/... + context  →  downstream crew inputs
```

## Error Handling

- **Faithfulness gate (critical):** the enrich agent is constrained to *reorganize and
  clarify only — never invent* facts. It must not fabricate budget, dates, traveler
  counts, or preferences the user did not state. The task prompt states this explicitly
  with a negative example. This is the primary risk of a "improve the prompt" step and
  the main thing tests must defend.
- **Fallback:** if `enrich_request_task` output is empty or unusable, extraction and
  `state.enriched_brief` both fall back to the raw request — behavior is never worse
  than today.
- **Backstop:** the already-shipped road-trip fallback in `generate_holiday_plan`
  remains, so even a degraded enrich/extract cannot reintroduce the empty-destination
  failure.

## Testing

1. **Enrich quality:** the multi-city French request yields a brief containing all four
   cities and the dates. Uses a canned/stubbed LLM output for determinism (no live LLM
   in CI).
2. **Wiring:** `extract_info` populates `state.enriched_brief`; `to_crew_inputs()` maps
   it to `context`.
3. **Faithfulness regression:** faithfulness is enforced at the prompt level ("clarify,
   never invent"). The test uses a canned enrich output for a minimal request ("write a
   poem about Rome") and asserts the resulting `ExtractedInfo` and `context` introduce
   no travel/budget/traveler fields that were absent from the source — i.e. enrichment
   did not fabricate structure.
4. **Fallback:** empty enrich output → extraction still runs on the raw request and
   `state.enriched_brief` equals the raw request.

## Cost

Adds **one LLM call per request** (all requests, not just travel), sized to the "quick"
timeout. Accepted for the across-the-board quality lift.

## Related

- Shipped guard/fallback: `tests/flows/test_holiday_no_destination.py`,
  `src/epic_news/main.py` (`CLASSIFY_DECISION_FILE`, holiday fallback).
- Extraction crew: `src/epic_news/crews/information_extraction/`.
