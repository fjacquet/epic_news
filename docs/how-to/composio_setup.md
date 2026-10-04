# Composio Setup Guide for Epic News

## Overview

Composio provides hosted integrations for agentic workflows. epic_news uses it for two things:

1. **Social search tools** for the `company_news` crew (Reddit, Twitter, Hacker News).
2. **Report email delivery** through Gmail (`GMAIL_SEND_EMAIL`), called directly by the flow, not by an agent.

**Important**: epic_news uses the Composio 1.0 API (`Composio(..., provider=CrewAIProvider())`). The old `ComposioToolSet` API is deprecated.

## Quick Start

### 1. Get Your Composio API Key

1. Sign up at [https://app.composio.dev](https://app.composio.dev)
2. Navigate to **Settings → API Keys**
3. Copy your API key

### 2. Add API Key to Environment

Add to your `.env` file:

```bash
# Composio Configuration
COMPOSIO_API_KEY=your_composio_api_key_here
```

### 3. Test Connection

```bash
# Test Composio connection
uv run python -c "
from epic_news.config.composio_config import ComposioConfig

config = ComposioConfig()
print('✓ Composio configured successfully')
print(f'✓ Search tools available: {len(config.get_search_tools())}')
"
```

## What epic_news Uses

`ComposioConfig` (`src/epic_news/config/composio_config.py`) exposes:

| Method | Returns | Used by |
|---|---|---|
| `get_search_tools()` | Search tools from Reddit, Twitter and Hacker News | `company_news` crew |
| `get_gmail_email_tools(include_send=True)` | Gmail toolkit tools for an agent | Not used by any crew |

Email delivery does not go through an agent: `epic_news.utils.email_sender.send_report_email()` executes `GMAIL_SEND_EMAIL` with the Composio client.

### 1. Search Tools (From Social Media Platforms)

Composio 1.0 has **no dedicated "SEARCH" toolkit**. `get_search_tools()` loads the Reddit, Twitter and Hacker News toolkits and keeps the tools whose name contains `search`:

- `REDDIT_SEARCH_ACROSS_SUBREDDITS`: Search Reddit for topics
- `REDDIT_GET_SUBREDDITS_SEARCH`: Find relevant subreddits
- `TWITTER_FULL_ARCHIVE_SEARCH`: Search Twitter posts (requires Twitter connection)
- `HACKERNEWS_SEARCH_POSTS`: Search Hacker News stories (no auth required)

A toolkit that fails to load is logged and skipped, so the list can be shorter than expected.

**Connect Reddit / Twitter**:

1. Go to the [Composio Dashboard](https://app.composio.dev/apps)
2. Find **Reddit** or **Twitter** and click **Connect**
3. Authorize Composio (read and search permissions are enough)

Hacker News needs no connection.

### 2. Gmail (Report Email)

**Setup**:

1. In the Composio Dashboard, add a **Gmail** connection under the user/entity ID `default`
2. Set `EPIC_ENABLE_EMAIL=true` in `.env` (email is skipped otherwise)
3. Set `MAIL` to the recipient address

`send_report_email()` validates the recipient and body, uploads the attachment from the output directory (`EPIC_OUTPUT_DIR`, default `output`), calls `GMAIL_SEND_EMAIL` and raises `EmailDeliveryError` unless Composio reports success.

Manual tool execution needs a pinned toolkit version. The default is set in `email_sender.py`; override it with `COMPOSIO_GMAIL_VERSION` when Composio publishes a new Gmail toolkit version.

## Testing Your Setup

```python
from epic_news.config.composio_config import ComposioConfig

config = ComposioConfig()

search_tools = config.get_search_tools()
print(f"✓ {len(search_tools)} search tools: {[t.name for t in search_tools]}")

gmail_tools = config.get_gmail_email_tools(include_send=True)
print(f"✓ Gmail tools: {[t.name for t in gmail_tools]}")
```

If `GMAIL_SEND_EMAIL` is missing from the Gmail list, your Gmail connection or Composio plan does not expose it.

## Troubleshooting

### Issue: "COMPOSIO_API_KEY environment variable is required"

**Solutions**:

1. Ensure `COMPOSIO_API_KEY` is set in `.env`
2. Restart your terminal/IDE to reload environment
3. Verify the key is valid at https://app.composio.dev

### Issue: "Could not load {PLATFORM} search tools from Composio"

**Solutions**:

1. Check that the app is connected in the Composio Dashboard
2. Check app permissions
3. For OAuth apps, re-authenticate if the token expired

### Issue: Email not delivered

See [Troubleshooting → I didn't receive the email](troubleshooting.md#i-didnt-receive-the-email).

## Additional Resources

- [Composio Documentation](https://docs.composio.dev/)
- [Composio App Catalog](https://app.composio.dev/apps)
- [Composio API Reference](https://docs.composio.dev/api-reference)
- [CrewAI + Composio Integration](https://docs.crewai.com/tools/composio)
