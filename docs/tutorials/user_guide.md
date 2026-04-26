# User Guide

This is the entry point for **using** Epic News. If you want to build a new crew or set up the dev environment, see [Your First Crew](getting_started.md) and [Development Setup](../how-to/development_setup.md) instead.

## How to Use Epic News

1. **Start the application:** `crewai flow kickoff`
2. **Type a request** in plain English or French — no special syntax.
3. **Wait for the report.** Epic News classifies your request, picks the right crew, and writes the result to `output/<crew>/`.
4. **Check your inbox.** If Gmail is connected via Composio, you also receive the HTML report by email.

## Use Cases by Category

The full list of crews is split into four pages by domain:

| Category | What's inside |
|---|---|
| 📈 [Finance](use_cases/finance.md) | FinDailyCrew (portfolio analysis), Shopping Advisor |
| 📰 [News & Research](use_cases/news_research.md) | Daily news, RSS weekly, Company news, PESTEL, Deep research, Book summary |
| 💼 [Business & Intelligence](use_cases/business_intel.md) | Sales prospecting, Meeting prep, OSINT, Legal analysis |
| 🍳 [Lifestyle & Creative](use_cases/lifestyle.md) | Cooking, Menu planning, Travel, Saint of the day, Poem |

## After a Run

- Where things land on disk, what the logs mean, how to read trace events:
  → [Output Reference](../reference/outputs.md)
- Email didn't arrive? Wrong crew triggered? Diagnose with:
  → [Troubleshooting & FAQ](../how-to/troubleshooting.md)

## Going Further

- [Build Your First Crew](getting_started.md) — step-by-step tutorial.
- [Architecture Overview](../explanations/architecture.md) — how the flow, classifier and renderers fit together.
- [Architecture Decision Records](../adr/) — why things are built the way they are.
