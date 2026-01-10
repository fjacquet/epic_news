# Composio Setup Guide for Epic News

## Overview

Composio provides 500+ integrations for agentic workflows. This guide explains how to set up Composio for the epic_news project.

**Important**: epic_news uses **Composio 1.0.0-rc2** with the new API. The old `ComposioToolSet` API is deprecated.

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

## Available Tool Categories

### 1. Search Tools (From Social Media Platforms)

**IMPORTANT**: Composio 1.0 has **NO dedicated "SEARCH" toolkit**. Search functionality comes from social media platforms.

**Available Search Tools**:
- `REDDIT_SEARCH_ACROSS_SUBREDDITS`: Search Reddit for topics
- `REDDIT_GET_SUBREDDITS_SEARCH`: Find relevant subreddits
- `TWITTER_FULL_ARCHIVE_SEARCH`: Search Twitter posts (requires Twitter connection)
- `HACKERNEWS_SEARCH_POSTS`: Search Hacker News stories (no auth required)

**Usage**:
```python
from epic_news.config.composio_config import ComposioConfig

config = ComposioConfig()
search_tools = config.get_search_tools()  # Returns search tools from Reddit/Twitter/HackerNews
```

**Status**: ⚠️ **Partially ready** (HackerNews works without auth; Reddit/Twitter require connection)

---

### 2. Social Media Tools

#### Reddit

**Setup**:
1. Go to [Composio Dashboard](https://app.composio.dev/apps)
2. Find **Reddit** in the apps list
3. Click **Connect**
4. Authorize Composio to access your Reddit account
5. Select permissions: Read posts, Search, Get user info

**Available Actions**:
- Get trending posts from subreddits
- Search Reddit for topics
- Get post comments
- Analyze Reddit discussions

**Usage**:
```python
config = ComposioConfig()
reddit_tools = config.get_social_media_tools(platforms=['REDDIT'])
```

**Status**: ⚠️ **Requires Reddit account connection**

#### Twitter

**Setup**:
1. Go to [Composio Dashboard](https://app.composio.dev/apps)
2. Find **Twitter** in the apps list
3. Click **Connect**
4. Authorize via Twitter OAuth
5. Grant read permissions

**Available Actions**:
- Search tweets
- Get trending topics
- Analyze tweet sentiment
- Get user timelines

**Usage**:
```python
config = ComposioConfig()
twitter_tools = config.get_social_media_tools(platforms=['TWITTER'])
```

**Status**: ⚠️ **Requires Twitter account connection**

#### Hacker News

**Setup**: None required (public API)

**Available Actions**:
- Get top stories
- Get new stories
- Get best stories
- Search Hacker News

**Usage**:
```python
config = ComposioConfig()
hn_tools = config.get_social_media_tools(platforms=['HACKERNEWS'])
```

**Status**: ✅ **Ready to use** (no authentication required)

---

### 3. Financial Tools

#### Alpha Vantage

**Setup**:
1. Get free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. In Composio Dashboard, go to **Apps → Alpha Vantage**
3. Click **Connect**
4. Enter your Alpha Vantage API key

**Available Actions**:
- Get stock quotes
- Get historical stock data
- Get technical indicators
- Currency exchange rates

**Usage**:
```python
config = ComposioConfig()
financial_tools = config.get_financial_tools()
```

**Status**: ⚠️ **Requires Alpha Vantage API key**

#### CoinMarketCap

**Setup**:
1. Get API key from [CoinMarketCap](https://coinmarketcap.com/api/)
2. In Composio Dashboard, go to **Apps → CoinMarketCap**
3. Click **Connect**
4. Enter your CoinMarketCap API key

**Available Actions**:
- Get cryptocurrency listings
- Get crypto prices
- Get market data
- Historical crypto data

**Usage**:
```python
config = ComposioConfig()
financial_tools = config.get_financial_tools()
```

**Status**: ⚠️ **Requires CoinMarketCap API key**

---

### 4. Communication & Collaboration Tools

#### Slack

**Setup**:
1. In Composio Dashboard, go to **Apps → Slack**
2. Click **Connect**
3. Select your Slack workspace
4. Authorize Composio app
5. Select channels to allow access

**Available Actions**:
- Send messages to channels
- Post crew results to Slack
- Create threads
- Upload files

**Usage**:
```python
config = ComposioConfig()
comm_tools = config.get_communication_tools()

# Example: Send crew results to Slack
# slack_send = next(t for t in comm_tools if 'send_message' in t.name)
```

**Status**: ⚠️ **Requires Slack workspace connection**

**Use Case**: Notify team when deep_research report is ready

#### Discord

**Setup**:
1. In Composio Dashboard, go to **Apps → Discord**
2. Click **Connect**
3. Authorize Composio bot to your Discord server
4. Select permissions: Send Messages, Read Messages

**Available Actions**:
- Send messages to Discord channels
- Post notifications
- Create embeds

**Status**: ⚠️ **Requires Discord server connection**

#### Notion

**Setup**:
1. In Composio Dashboard, go to **Apps → Notion**
2. Click **Connect**
3. Authorize Composio to access your Notion workspace
4. Select pages/databases to allow access

**Available Actions**:
- Create pages
- Store research reports
- Update databases
- Query databases

**Usage**:
```python
config = ComposioConfig()
comm_tools = config.get_communication_tools()
```

**Status**: ⚠️ **Requires Notion workspace connection**

**Use Case**: Save deep_research reports to Notion knowledge base

#### Gmail

**Setup**: Already configured in project

**Status**: ✅ **Ready to use**

---

### 5. Content Creation Tools

#### Canva

**Setup**:
1. In Composio Dashboard, go to **Apps → Canva**
2. Click **Connect**
3. Authorize Composio to access your Canva account

**Available Actions**:
- Create designs from templates
- Generate social media graphics
- Export designs

**Status**: ⚠️ **Requires Canva account connection**

**Use Case**: Generate visual content for social media posts

#### Airtable

**Setup**:
1. Get Airtable API key from [Airtable Account](https://airtable.com/account)
2. In Composio Dashboard, go to **Apps → Airtable**
3. Click **Connect**
4. Enter your Airtable API key
5. Select bases to allow access

**Available Actions**:
- Create records
- Store crew outputs
- Query tables
- Update records

**Status**: ⚠️ **Requires Airtable API key**

**Use Case**: Store news articles, research findings, and crew outputs

---

## Integration Checklist

Use this checklist to track which integrations you've set up:

**IMPORTANT**: Composio 1.0 provides 171 tools across 10 toolkits (as of current setup):
- REDDIT (19 tools), TWITTER (20 tools), HACKERNEWS (6 tools)
- GMAIL (20 tools), SLACK (20 tools), DISCORD (15 tools), NOTION (20 tools)
- CANVA (20 tools), AIRTABLE (20 tools), COINMARKETCAP (11 tools)

### Free (No Setup Required)
- ⚠️ ~~Search Tools (SEARCH app)~~ **DOES NOT EXIST in Composio 1.0**
  - Use `get_search_tools()` to get search from Reddit/Twitter/HackerNews instead
- [x] Hacker News (6 tools including HACKERNEWS_SEARCH_POSTS)

### Requires Free API Keys
- [ ] Alpha Vantage (free tier: 25 requests/day)

### Requires Account Connection
- [ ] Reddit
- [ ] Twitter
- [ ] Slack
- [ ] Discord
- [ ] Notion
- [ ] Gmail (already set up)
- [ ] Canva
- [ ] Airtable

### Requires Paid API Keys
- [ ] CoinMarketCap (paid plans for higher limits)

## Testing Your Setup

### Test Individual Tool Categories

```python
from epic_news.config.composio_config import ComposioConfig

config = ComposioConfig()

# Test search tools (should always work)
print("Testing search tools...")
search_tools = config.get_search_tools()
print(f"✓ {len(search_tools)} search tools available")

# Test social media tools (requires connections)
print("\nTesting social media tools...")
try:
    social_tools = config.get_social_media_tools()
    print(f"✓ {len(social_tools)} social media tools available")
except Exception as e:
    print(f"✗ Social media tools not available: {e}")

# Test financial tools (requires API keys)
print("\nTesting financial tools...")
try:
    financial_tools = config.get_financial_tools()
    print(f"✓ {len(financial_tools)} financial tools available")
except Exception as e:
    print(f"✗ Financial tools not available: {e}")

# Test communication tools
print("\nTesting communication tools...")
try:
    comm_tools = config.get_communication_tools()
    print(f"✓ {len(comm_tools)} communication tools available")
except Exception as e:
    print(f"✗ Communication tools not available: {e}")

# Test content creation tools
print("\nTesting content creation tools...")
try:
    content_tools = config.get_content_creation_tools()
    print(f"✓ {len(content_tools)} content creation tools available")
except Exception as e:
    print(f"✗ Content creation tools not available: {e}")
```

## Troubleshooting

### Issue: "API Key not provided"

**Symptoms**: `composio.exceptions.ApiKeyNotProvidedError`

**Solutions**:
1. Ensure `COMPOSIO_API_KEY` is set in `.env`
2. Restart your terminal/IDE to reload environment
3. Verify key is valid at https://app.composio.dev

### Issue: "Could not load {APP} tools"

**Symptoms**: Warning messages when initializing tools

**Solutions**:
1. Check if you've connected the app in Composio Dashboard
2. For API-based apps, verify API key is correct
3. Check app permissions in Composio Dashboard
4. Some apps may require paid Composio plan

### Issue: Tools not working in crews

**Symptoms**: Crew fails when trying to use tool

**Solutions**:
1. Verify integration is active in Composio Dashboard
2. Check tool permissions (read, write, etc.)
3. For OAuth apps, re-authenticate if token expired
4. Check Composio Dashboard logs for API errors

## Recommended Setup for Epic News

For the epic_news project, we recommend setting up these integrations:

### Priority 1 (High Value)
1. ✅ **Search Tools** - Already working
2. **Reddit** - For news discovery and trend analysis
3. **Hacker News** - For tech news aggregation
4. **Slack** - For crew notifications

### Priority 2 (Useful)
5. **Notion** - For storing research reports
6. **Twitter** - For real-time social media trends

### Priority 3 (Optional)
7. **Alpha Vantage** - For financial news crews
8. **Discord** - Alternative to Slack
9. **Airtable** - For structured data storage

## Usage in Crews

### Example: company_news Crew with Social Media

```python
from epic_news.config.composio_config import ComposioConfig
from epic_news.config.llm_config import LLMConfig

@CrewBase
class CompanyNewsCrew:
    def __init__(self):
        # Get Composio tools
        composio = ComposioConfig()
        self.search_tools = composio.get_search_tools()
        self.social_tools = composio.get_social_media_tools(platforms=['REDDIT', 'HACKERNEWS'])

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=self.search_tools + self.social_tools,  # Combine tools
            llm=LLMConfig.get_openrouter_llm(),
            verbose=True,
        )
```

## Additional Resources

- [Composio Documentation](https://docs.composio.dev/)
- [Composio App Catalog](https://app.composio.dev/apps)
- [Composio API Reference](https://docs.composio.dev/api-reference)
- [CrewAI + Composio Integration](https://docs.crewai.com/tools/composio)

## Getting Help

If you encounter issues:

1. Check [Composio Discord](https://discord.gg/composio) for community support
2. Review [Composio GitHub Issues](https://github.com/ComposioHQ/composio/issues)
3. Contact Composio support at support@composio.dev
