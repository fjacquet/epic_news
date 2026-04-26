# Epic News Crew

[![CI](https://github.com/fjacquet/epic_news/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/fjacquet/epic_news/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/fjacquet/epic_news)](https://github.com/fjacquet/epic_news/releases/latest)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/downloads/release/python-3130/)
[![CrewAI](https://img.shields.io/badge/crewAI-1.14%2B-purple)](https://crewai.com)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Natural-language AI assistant for financial analysis, news, research, recipes, travel, OSINT, and more. Built on [crewAI](https://crewai.com): ask in plain English or French and the right team of AI agents (a "crew") handles your request.

## TL;DR

```bash
pip install uv
uv sync && uv pip install -e .
cp .env.example .env       # then add your API keys
crewai flow kickoff        # type a request when prompted
```

Reports land in `output/<crew>/` and (if Gmail is connected via Composio) in your inbox.

## Documentation

The full documentation lives in [`docs/`](./docs/index.md), organized in the [Diátaxis](https://diataxis.fr/) style.

| If you want to… | Go to |
|---|---|
| **Discover what you can ask the system** | [User Guide](./docs/tutorials/user_guide.md) |
| **Build your first crew** | [Tutorial: Your First Crew](./docs/tutorials/getting_started.md) |
| **Set up the dev environment** | [Development Setup](./docs/how-to/development_setup.md) |
| **Understand the architecture** | [Architecture](./docs/explanations/architecture.md) |
| **Browse Architecture Decision Records** | [`docs/adr/`](./docs/adr/) |
| **See what changed** | [CHANGELOG.md](./CHANGELOG.md) |

## Project Highlights

- **~25 specialized crews** — finance, news, OSINT, cooking, legal, sales, travel, deep research, PESTEL…
- **Real-time data over RAG** — agents call live tools (Perplexity, Tavily, YahooFinance, …) per execution
- **Deterministic HTML rendering** — Pydantic models → BeautifulSoup → single consolidated stylesheet inlined at render time (email-safe, print-friendly)
- **Composable observability** — loguru trace per run, structured `PostResult` for email outcomes, page-break-aware print mode (Arial Nova Light @ 9pt)

## Contributing

PRs welcome. Please run `make validate` (lint + tests) before opening one. See the [Development Setup](./docs/how-to/development_setup.md) for the full workflow.

## Support

- [crewAI documentation](https://docs.crewai.com)
- [Issue tracker](https://github.com/fjacquet/epic_news/issues)
