# API Keys Reference

Complete reference for all API keys required by Epic News tools and services.

## Quick Setup

Copy this template to your `.env` file and fill in the required keys:

```bash
# =============================================================================
# REQUIRED - Core functionality
# =============================================================================

# LLM Provider (Required)
OPENROUTER_API_KEY=your_openrouter_api_key

# Search (At least one required)
PERPLEXITY_API_KEY=pplx-xxxx                    # Primary search
SERPER_API_KEY=xxxx                              # Fallback search

# =============================================================================
# RECOMMENDED - Enhanced functionality
# =============================================================================

# Web Scraping (One required for content extraction)
RAPIDAPI_KEY=xxxx                                # ScrapeNinja (default)
FIRECRAWL_API_KEY=fc-xxxx                        # Alternative scraper

# Additional Search
BRAVE_API_KEY=xxxx                               # Brave Search
TAVILY_API_KEY=tvly-xxxx                         # Tavily Search

# =============================================================================
# OPTIONAL - Feature-specific
# =============================================================================

# Financial Data
ALPHA_VANTAGE_API_KEY=xxxx                       # Stock fundamentals
X-CMC_PRO_API_KEY=xxxx                           # CoinMarketCap crypto
OPENEXCHANGERATES_API_KEY=xxxx                   # Currency exchange
KRAKEN_API_KEY=xxxx                              # Kraken crypto exchange

# Location & Weather
ACCUWEATHER_API_KEY=xxxx                         # Weather forecasts
GEOAPIFY_API_KEY=xxxx                            # Place search

# Business Intelligence
HUNTER_API_KEY=xxxx                              # Email finding
GITHUB_TOKEN=ghp_xxxx                            # GitHub API

# Productivity
AIRTABLE_API_KEY=xxxx                            # Airtable integration
TODOIST_API_KEY=xxxx                             # Todoist tasks
COMPOSIO_API_KEY=xxxx                            # Composio tools

# Fact Checking
GOOGLE_API_KEY=xxxx                              # Google Fact Check API
SERPAPI_API_KEY=xxxx                             # SerpAPI
```

## Detailed Reference

### Core Services

| Key | Service | Required | Free Tier | Get Key |
|-----|---------|----------|-----------|---------|
| `OPENROUTER_API_KEY` | OpenRouter LLM | **Yes** | $5 credit | [openrouter.ai](https://openrouter.ai) |
| `PERPLEXITY_API_KEY` | Perplexity AI Search | **Yes*** | Limited | [perplexity.ai](https://perplexity.ai) |
| `SERPER_API_KEY` | Serper.dev | **Yes*** | 2,500/month | [serper.dev](https://serper.dev) |

*At least one search provider required

### Search Providers

| Key | Service | Purpose | Free Tier | Get Key |
|-----|---------|---------|-----------|---------|
| `PERPLEXITY_API_KEY` | Perplexity | AI-powered search with synthesis | Limited | [perplexity.ai](https://perplexity.ai) |
| `SERPER_API_KEY` | Serper.dev | Google search results | 2,500/month | [serper.dev](https://serper.dev) |
| `BRAVE_API_KEY` | Brave Search | Privacy-focused search | 2,000/month | [brave.com/search/api](https://brave.com/search/api) |
| `TAVILY_API_KEY` | Tavily | Research-optimized search | 1,000/month | [tavily.com](https://tavily.com) |
| `SERPAPI_API_KEY` | SerpAPI | Multi-engine search | 100/month | [serpapi.com](https://serpapi.com) |

### Web Scraping

| Key | Service | Purpose | Free Tier | Get Key |
|-----|---------|---------|-----------|---------|
| `RAPIDAPI_KEY` | ScrapeNinja | Default web scraper | Limited | [rapidapi.com](https://rapidapi.com) |
| `FIRECRAWL_API_KEY` | Firecrawl | Alternative scraper | 500/month | [firecrawl.dev](https://firecrawl.dev) |

**Configuration:**
```bash
# Select scraper provider (default: scrapeninja)
WEB_SCRAPER_PROVIDER=scrapeninja  # or "firecrawl"
```

### Financial Data

| Key | Service | Purpose | Free Tier | Get Key |
|-----|---------|---------|-----------|---------|
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage | Stock fundamentals | 25/day | [alphavantage.co](https://alphavantage.co) |
| `X-CMC_PRO_API_KEY` | CoinMarketCap | Crypto data | 333/day | [coinmarketcap.com](https://coinmarketcap.com/api) |
| `OPENEXCHANGERATES_API_KEY` | Open Exchange Rates | Currency rates | 1,000/month | [openexchangerates.org](https://openexchangerates.org) |
| `KRAKEN_API_KEY` | Kraken | Crypto exchange | Unlimited | [kraken.com](https://kraken.com) |

### Location & Weather

| Key | Service | Purpose | Free Tier | Get Key |
|-----|---------|---------|-----------|---------|
| `ACCUWEATHER_API_KEY` | AccuWeather | Weather forecasts | 50/day | [developer.accuweather.com](https://developer.accuweather.com) |
| `GEOAPIFY_API_KEY` | Geoapify | Place search, geocoding | 3,000/day | [geoapify.com](https://geoapify.com) |

### Business Intelligence

| Key | Service | Purpose | Free Tier | Get Key |
|-----|---------|---------|-----------|---------|
| `HUNTER_API_KEY` | Hunter.io | Email finding | 25/month | [hunter.io](https://hunter.io) |
| `GITHUB_TOKEN` | GitHub | Repository data | 5,000/hour | [github.com/settings/tokens](https://github.com/settings/tokens) |

### Productivity

| Key | Service | Purpose | Free Tier | Get Key |
|-----|---------|---------|-----------|---------|
| `AIRTABLE_API_KEY` | Airtable | Database integration | Yes | [airtable.com](https://airtable.com/account) |
| `TODOIST_API_KEY` | Todoist | Task management | Yes | [todoist.com](https://todoist.com/app/settings/integrations) |
| `COMPOSIO_API_KEY` | Composio | Tool integrations | Yes | [composio.dev](https://composio.dev) |

### Fact Checking

| Key | Service | Purpose | Free Tier | Get Key |
|-----|---------|---------|-----------|---------|
| `GOOGLE_API_KEY` | Google Fact Check | Claim verification | Yes | [console.cloud.google.com](https://console.cloud.google.com) |

## Search Provider Hierarchy

Epic News uses a cascading fallback for search:

```
1. Perplexity (Primary)    → AI-powered synthesis with citations
   ↓ (if unavailable)
2. Brave Search            → Quality web results
   ↓ (if unavailable)
3. Serper                  → Google search results
   ↓ (if unavailable)
4. Serper News             → News-specific search
```

## Minimum Viable Setup

For basic functionality, you need only:

```bash
# Minimum required
OPENROUTER_API_KEY=your_key    # LLM provider
PERPLEXITY_API_KEY=your_key    # Primary search
RAPIDAPI_KEY=your_key          # Web scraping
```

## Validation

Check your API keys are configured:

```bash
# List configured keys
grep "_API_KEY\|_TOKEN" .env | grep -v "^#"

# Test a specific tool
uv run python -c "
from epic_news.tools.perplexity_search_tool import PerplexitySearchTool
tool = PerplexitySearchTool()
print(f'Perplexity configured: {tool.api_key is not None}')
"
```

## Troubleshooting

### Key Not Found Errors

```
ValueError: SERPER_API_KEY environment variable not set
```

**Solutions:**
1. Verify key exists in `.env` file
2. Check for typos in key name
3. Ensure no trailing whitespace
4. Restart terminal/IDE after adding keys

### Invalid Key Errors

```
401 Unauthorized
```

**Solutions:**
1. Verify key is valid and not expired
2. Check API dashboard for usage limits
3. Regenerate key if compromised

### Rate Limit Errors

```
429 Too Many Requests
```

**Solutions:**
1. Wait and retry (automatic with hybrid search)
2. Configure backup providers
3. Upgrade API plan if needed

## Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use `.env.example`** - Template without real values
3. **Rotate keys regularly** - Especially after exposure
4. **Limit key permissions** - Use minimal required scope
5. **Monitor usage** - Check API dashboards regularly

## Related Documentation

- [Development Setup](../how-to/development_setup.md) - Environment configuration
- [Tools Reference](tools.md) - Complete tool documentation
- [Troubleshooting](../troubleshooting/common_errors.md) - Common issues
