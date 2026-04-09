# ADR-009: Composio 1.0 Integration for External Service Tools

## Status

Accepted

## Context

Crews need to interact with external services (Gmail, Slack, Discord, Reddit, Twitter, CoinMarketCap) for communication and data gathering. Building custom integrations for each service would be maintenance-heavy. Composio provides a unified API for 100+ services with OAuth management.

## Decision

- Use Composio 1.0 API via `ComposioConfig` factory class (`src/epic_news/config/composio_config.py`)
- Organize tools by category: `get_search_tools()`, `get_communication_tools()`, `get_financial_tools()`, `get_content_creation_tools()`
- Graceful degradation: missing `COMPOSIO_API_KEY` returns empty tool lists instead of crashing
- Gmail uses `CREATE_EMAIL_DRAFT` action (not deprecated `GMAIL_SEND_EMAIL`)
- Requires `COMPOSIO_API_KEY` in `.env`

## Consequences

- Unified authentication and tool interface for 10+ external services
- Adding new service integrations requires only Composio action configuration, not custom code
- Composio manages OAuth token refresh — no manual credential rotation
- Vendor dependency on Composio for external service access
- One crew (`company_news`) still uses deprecated Composio API — migration pending
