# Use Cases — News & Research

This page lists the crews focused on news aggregation, weekly digests, and research.

[← Back to User Guide](../user_guide.md)

## 📰 Daily News (NewsDailyCrew)

**What it does:** Curates the top 10 daily news items across 7 categories (Suisse Romande, Suisse, France, Europe, World, Wars, Economy) with deduplication and professional French formatting.

**Sample prompts:**

- "Generate daily news report."
- "Donne-moi les actualités du jour."
- "Get the top 10 news for Switzerland, France, Europe and world."

**Output:** Structured French HTML news report by region/category.

## 📡 RSS Weekly (RssWeeklyCrew)

**What it does:** Generates a weekly digest from your RSS feeds defined in `data/feedly.opml`.

**Sample prompts:**

- "Generate my weekly RSS summary."
- "What happened this week in my feeds?"
- "Weekly tech news roundup."

**Output:** HTML report grouping articles per feed.

## 📰 Company News (CompanyNewsCrew)

**What it does:** Researches and summarizes news topics with multiple research and fact-checking agents.

**Sample prompts:**

- "Summarize the latest tech news."
- "Give me a report on AI news this week."

**Output:** Well-structured news report with citations.

## 🌐 PESTEL Analysis (PestelCrew)

**What it does:** Strategic macro-environmental analysis (Political, Economic, Social, Technological, Environmental, Legal) for a company, country, or sector.

**Sample prompts:**

- "Faire un rapport PESTEL sur la société Temenos en français."
- "PESTEL analysis of the EU electric vehicle market."

**Output:** Structured HTML PESTEL report by dimension.

## 🔬 Deep Research (DeepResearchCrew)

**What it does:** Academic-grade quantitative research with statistical analysis on any topic. Uses an iterative replanning loop with quality gates.

**Sample prompts:**

- "Conduct a deep research study on quantum computing for cryptography."
- "Deep research on Mediterranean diet long-term health outcomes."

**Output:** Long-form research report with sources and quantitative analysis.

## 📚 Book Summary (LibraryCrew)

**What it does:** Generates comprehensive book summaries with key insights and takeaways.

**Sample prompts:**

- "Summarize 'Le Petit Prince' and suggest similar books."
- "Summarize 'The Lean Startup'."
- "Book summary of 'Atomic Habits'."

**Output:** Structured book summary (HTML).

---

See also: [Finance](finance.md) · [Business & Intelligence](business_intel.md) · [Output Reference](../../reference/outputs.md)
