# Troubleshooting & FAQ

Common issues and how to diagnose them.

## My request triggered the wrong crew (or got partial answer)

Rephrase or split into two sentences. The classifier looks at the verbs and
domain keywords; an ambiguous prompt like *"tell me about Apple"* may
trigger `news_daily` rather than `company_profiler`. Try
*"Generate a company profile for Apple Inc."* instead.

## I see no HTML/JSON output for a crew

1. Check `output/<crew>/` — file may exist but with a slightly different
   name than expected.
2. Check `logs/epic_news.log` for an `❌` line near the end of the run.
3. Some crews (RSS weekly, holiday planner) write the JSON before the HTML
   step — if HTML failed, JSON will still be there.

## I didn't receive the email

Open `logs/epic_news.log` and look for the `📨 PostResult` line:

- **`status=success`** → email **was** delivered. Check spam folder, and
  verify `MAIL` in `.env` points to the address you actually check (not the
  default `fred.jacquet@gmail.com`).
- **`status=failure`** → read `error_message`:
  - *"No connected account found for user ID default for toolkit gmail"* →
    you need to authorize Gmail in Composio under entity `default`. Go to
    [app.composio.dev](https://app.composio.dev), Connections → Add
    connection → Gmail → use `default` as user/entity ID.
  - *"Failed to read content from output_file: …/report.html"* → the
    upstream HTML rendering failed; look earlier in the log for an `❌`
    line. The v2.1.0 attachment guard now drops missing files
    automatically.
- **No `📨` line at all** → the `send_email` step never reached PostCrew.
  Look for `📬 Preparing to send email...` then check what came right
  after.

## Composio Gmail tool returns a draft instead of sending

In v2.1.0+ the PostCrew explicitly requests `GMAIL_SEND_EMAIL` first and
only falls back to `GMAIL_CREATE_EMAIL_DRAFT` if Composio doesn't return
the send variant (typically a paid-plan limitation). Run

```bash
uv run python -c "from epic_news.config.composio_config import ComposioConfig; print([t.name for t in ComposioConfig().get_gmail_email_tools(include_send=True)])"
```

If `GMAIL_SEND_EMAIL` is missing from the list, your Composio plan does
not expose it — re-OAuth or upgrade.

## API errors

Ensure `.env` is set up against `.env.example`. Common required keys:

- `OPENROUTER_API_KEY`, `MODEL`
- `COMPOSIO_API_KEY` (for Gmail, Notion, Slack, …)
- `RAPIDAPI_KEY` (ScrapeNinja default scraper)
- `FIRECRAWL_API_KEY` (alternative scraper)
- `KRAKEN_API_KEY`, `KRAKEN_API_SECRET` (FinDailyCrew crypto)
- `SERPAPI_API_KEY`, `TAVILY_API_KEY`, `EXA_API_KEY` (search providers)

## Old code runs after I edited a file

The CrewAI flow is a long-running process. If you launch a flow then
edit Python source while it's still running, the in-memory class
remains the old version. Cancel the flow and restart, or remove
`__pycache__/` if a `.pyc` got out of sync:

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
```

## Where to look next

- [Output Reference](../reference/outputs.md) — full map of `output/`,
  `logs/`, `traces/`, `debug/`
- [Development Setup](development_setup.md) — full dev workflow
- [crewAI documentation](https://docs.crewai.com)
- Open an issue on [GitHub](https://github.com/fjacquet/epic_news/issues)
