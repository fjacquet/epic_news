# Troubleshooting & FAQ

Common issues and how to diagnose them.

## My request triggered the wrong crew (or got partial answer)

Rephrase or split into two sentences. The classifier looks at the verbs and
domain keywords; an ambiguous prompt like *"tell me about Apple"* may
trigger `news_daily` rather than `company_profiler`. Try
*"Generate a company profile for Apple Inc."* instead.

## I see no DOCX/JSON output for a crew

1. Check `output/<crew>/` — file may exist but with a slightly different
   name than expected.
2. Check `logs/epic_news.log` for an `❌` line near the end of the run.
3. Some crews (RSS weekly, holiday planner) write the JSON before the
   DOCX step — if building the DOCX failed, the run stops and the JSON will
   still be there. Check that `pandoc` is installed (`pandoc --version`).

## I didn't receive the email

Email is sent only when `EPIC_ENABLE_EMAIL` is truthy (`true`, `1`, `yes`,
`on`); otherwise the step logs `✉️ Email sending disabled` and skips.
Delivery is deterministic: `ReceptionFlow.send_email` calls
`epic_news.utils.email_sender.send_report_email()`, which executes Composio
`GMAIL_SEND_EMAIL` directly (no agent). Open `logs/epic_news.log`:

- **`📨 Email delivered to …`** → Composio confirmed delivery. Check spam,
  and verify `MAIL` in `.env` points to the address you actually check.
- **`❌ Email NOT sent: …`** → `EmailDeliveryError`; read the message:
  - *"No connected account found for user ID default for toolkit gmail"* →
    authorize Gmail in Composio under entity `default`. Go to
    [app.composio.dev](https://app.composio.dev), Connections → Add
    connection → Gmail → use `default` as user/entity ID.
  - *"… is not a valid email address"* or *"Attachment does not exist"* →
    the inputs were rejected before any API call.
- **The report DOCX is missing** → nothing is sent and `email_sent` stays
  `False`; the email carries only a short body and the DOCX attachment.
  - A `ToolVersionRequiredError` / version error → set
    `COMPOSIO_GMAIL_VERSION` to a toolkit version your account exposes.
- **`🚫 No report was generated`** → the crew failed before writing a
  report; look earlier in the log for an `❌` line.
- **No `📤 Sending report` line** → the step returned early. Look for
  `📬 Preparing to send email...` and check what came right after.

## API errors

Ensure `.env` is set up against `.env.example`. Common required keys:

- `MODEL` (default `gemini/gemini-3.8-flash`) and `GEMINI_API_KEY`, or `OPENROUTER_API_KEY` for `openrouter/...` models
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
