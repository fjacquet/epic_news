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
| `📊 Crew <Name> took X.XXs — tokens: total=… prompt=… completion=… cached=… requests=…` | `kickoff_flow()` exit |
| `📬 Preparing to send email...` | `ReceptionFlow.send_email` start |
| `✉️  Email payload: recipient=… subject=… attachment=…` | Validated email inputs |
| `📤 Sending report to … (attachment=…)` | `send_report_email()` calls Composio `GMAIL_SEND_EMAIL` |
| `📨 Email delivered to …` | Composio confirmed delivery |
| `❌ Email NOT sent: …` | `EmailDeliveryError` — the message gives the cause |

`logs/epic_news_error.log` only receives `ERROR`/`CRITICAL` records.

## Traces

`traces/reception_flow_<timestamp>.json` is a JSONL file written by the
`Tracer` decorator (`@trace_task`). One JSON object per line, each capturing
`task_start` / `task_end` events with `timestamp`, `event_type`, `source`,
and a `details` dict.

Useful to verify a flow step actually ran (and how long it took) without
reading the full log.

## Email Outcome

Email delivery is deterministic: `ReceptionFlow.send_email` calls
`epic_news.utils.email_sender.send_report_email()`, which sends through
Composio `GMAIL_SEND_EMAIL` and raises `EmailDeliveryError` unless Composio
reports success. `state.email_sent` is `True` only after a confirmed
delivery (or when `EPIC_ENABLE_EMAIL` disables the step).

## Debug Dumps

`debug/crewai_state_<crew_name>_<timestamp>.json` — full CrewAI `result`
object dumped by `dump_crewai_state` for post-mortem analysis.

## Tracing the End-to-End Flow

1. User input → `extract_info` (trace event)
2. `classify` → picks the crew (trace event)
3. `generate_<crew>` → kickoff + render → writes to `output/<crew>/`
4. `send_email` → reads the report from `output/<crew>/` and sends it with `send_report_email()`

Run `tail -f logs/epic_news.log` during a flow to watch this live.
