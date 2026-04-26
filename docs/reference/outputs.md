# Output Reference

Where Epic News writes results, logs, and traces during a run.

## Generated Reports

Each crew writes to its own subdirectory under `output/`:

```
output/
├── pestel/
│   ├── report.html      # HTML rendition (sent as email body / attachment)
│   ├── report.json      # Structured data (Pydantic model dump)
│   └── report.md        # Markdown rendition (some crews)
├── rss_weekly/
│   ├── report.html
│   ├── final-report.json
│   └── report.json      # raw scraped articles before translation
├── poem/report.html
├── cooking/
│   ├── report.html
│   └── recipe.yaml      # Paprika-3-compatible YAML
└── …
```

The HTML inlines a single consolidated stylesheet (`templates/css/report.css`)
and a dynamic theme block (Arial Nova Light @ 9pt for print). Reports are
self-contained for email distribution.

## Logs

`logs/epic_news.log` is the **loguru** sink, written by every component that
uses `from loguru import logger` or `self.logger`. Useful breadcrumbs:

| Log line | Meaning |
|---|---|
| `📰 Generating RSS weekly report (new pipeline)...` | Crew start |
| `🚀 Kicking off crew <Name> with context keys: …` | `kickoff_flow()` entry |
| `✅ Crew <Name> finished in X.XXs` | `kickoff_flow()` exit |
| `📬 Preparing to send email...` | `ReceptionFlow.send_email` start |
| `✉️  Email payload: recipient=… subject=… attachment=…` | Pre-kickoff payload (v2.1.0+) |
| `🔧 Loading Gmail send tools from Composio...` | PostCrew tool discovery |
| `✅ Loaded N Gmail send tools: […]` | Tool list returned to the agent |
| `📨 PostResult: status=success recipient=… attachment_sent=…` | Email delivered |
| `❌ PostResult: status=failure recipient=… error_message=…` | Email failed — read `error_message` for the cause |

`logs/epic_news_error.log` only receives `ERROR`/`CRITICAL` records.

## Traces

`traces/reception_flow_<timestamp>.json` is a JSONL file written by the
`Tracer` decorator (`@trace_task`). One JSON object per line, each capturing
`task_start` / `task_end` events with `timestamp`, `event_type`, `source`,
and a `details` dict.

Useful to verify a flow step actually ran (and how long it took) without
reading the full log.

## Email Outcome (PostResult)

When the email step runs, the PostCrew agent is required to produce a
structured `PostResult`:

| Field | Description |
|---|---|
| `status` | `"success"` or `"failure"` |
| `recipient_email` | Final destination (typically `state.sendto` → `MAIL` env var) |
| `subject` | Subject line composed by the agent |
| `html_preserved` | `true` if HTML formatting was kept |
| `language_preserved` | `true` if no unintended translation happened |
| `attachment_sent` | `true` if a file was attached |
| `attachment_filename` | Filename if attached, else `"N/A"` |
| `error_message` | Full error from Composio if `status=failure`, else `"None"` |

Since v2.1.0 this object is parsed and logged via loguru in
`ReceptionFlow.send_email`, so failures surface in `epic_news.log` instead
of being lost between PostCrew's stdout and the missing email.

## Debug Dumps

`debug/crewai_state_<crew_name>_<timestamp>.json` — full CrewAI `result`
object dumped by `dump_crewai_state` for post-mortem analysis.

## Cache

`cache/yahoo_news_*.json`, `cache/<provider>_<query>.json` — request
caches honored by `requests-cache` and a few crew-specific caches.
Safe to delete; will be repopulated on next run.

## Tracing the End-to-End Flow

1. User input → `extract_info` (trace event)
2. `classify` → picks the crew (trace event)
3. `generate_<crew>` → kickoff + render → writes to `output/<crew>/`
4. `send_email` → reads from `output/<crew>/report.html`, kicks off PostCrew, parses `PostResult`

Run `tail -f logs/epic_news.log` during a flow to watch this live.
