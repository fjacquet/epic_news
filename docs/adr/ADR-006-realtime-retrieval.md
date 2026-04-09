# ADR-006: Real-Time Information Retrieval Over RAG

## Status

Accepted

## Context

Traditional RAG (Retrieval Augmented Generation) uses vector databases to store and retrieve documents. For a system analyzing financial markets, news, and current events, pre-indexed data becomes stale within hours. The project needed a strategy that prioritizes freshness over retrieval speed.

## Decision

- Use real-time tool-based retrieval instead of persistent vector databases
- Agents call live APIs on every execution: Perplexity, Tavily, YahooFinance, AlphaVantage, Brave Search
- `HybridSearchTool` implements cascading fallback (Perplexity → Brave → Serper) for resilience
- `SaveToRagTool` exists only as a short-term scratchpad within a single crew execution, not permanent storage
- No vector database infrastructure required

## Consequences

- Data is always fresh — critical for financial analysis (`fin_daily`) and news (`news_daily`)
- No ETL pipeline or embedding infrastructure to maintain
- Higher per-execution API costs compared to cached RAG
- Execution time depends on external API latency
- Cross-execution knowledge doesn't persist (by design — scoped memory fills this gap for agent learning)
