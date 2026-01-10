# 3. Epic News Architectural Patterns

This document describes key architectural patterns and solutions implemented in the Epic News system, with a strong focus on ensuring reliable, maintainable, and high-quality outputs.

## 1. HTML Rendering Architecture

The system employs a robust architecture for generating HTML reports, which has evolved to address several challenges. The core principle is to separate content generation from presentation, using deterministic Python-based rendering wherever possible.

### 1.1. Deterministic Python-Based Rendering

For crews with predictable and structured output (e.g., SAINT, POEM, FINDAILY), the system bypasses LLM-based HTML generation in favor of direct Python factory functions. This approach is faster, more reliable, and easier to maintain.

**Pattern:**

1. **Execute Crew**: The CrewAI flow runs as usual to generate the core content. The `.kickoff()` method returns a `CrewOutput` object.
2. **Parse to Pydantic Model**: The raw output from the crew is parsed into a structured Pydantic model (e.g., `SaintData`, `FinancialReport`).
3. **Render via Python Factory**: The Pydantic model is passed to a dedicated Python factory function (e.g., `saint_to_html`). This function uses a `TemplateManager` and a universal HTML template to produce the final, consistently styled report.

```python
# Example of the deterministic rendering flow
report_content = SaintDailyCrew().crew().kickoff(inputs=inputs)

# Parse the raw output into a structured Pydantic model
saint_model = SaintData.model_validate(json.loads(report_content.raw))

# Render the final HTML using a dedicated factory
saint_to_html(saint_model, html_file="output/saint_daily/report.html")
```

### 1.2. Data Routing: From Factory to Renderer

A common issue arises when the data structure produced by a crew's "HTML factory" does not match what the "HTML renderer" expects.

**Best Practice**:

- Ensure the data structure passed from the content-generating part of the crew to the renderer is consistent.
- Create a clear contract (e.g., via Pydantic models) between the data source and the renderer.
- Map fields explicitly to prevent mismatches (e.g., `link` → `url`, `published` → `date`).

### 1.3. HTML Rendering Best Practices

#### BeautifulSoup `class` Attribute Handling

**Issue**: BeautifulSoup's `class_` parameter can result in invalid HTML (`<div class_="...">`) which breaks CSS.

**Solution**: Always use the `attrs` dictionary or dictionary unpacking to set class attributes.

```python
# ✅ CORRECT - Using attrs dictionary
tag = soup.new_tag("div")
tag.attrs["class"] = ["container", "my-class"]

# ✅ ALSO CORRECT - Using dictionary unpacking
tag = soup.new_tag("div", **{"class": "container my-class"})

# ❌ PROBLEMATIC - Avoid this
tag = soup.new_tag("div", class_="container")
```

#### CSS Theme Compatibility

**Issue**: Hard-coded colors lead to poor readability in different UI themes (light/dark).

**Solution**: Use CSS variables with fallbacks for all color properties.

```css
/* ✅ CORRECT - Using CSS variables with fallbacks */
.element {
    color: var(--text-color, #343a40);
    background: var(--highlight-bg, #f8f9fa);
    border-color: var(--border-color, #dee2e6);
}
```

#### Markdown Link Parsing

**Issue**: Incorrect regex can fail to parse Markdown links `[text](url)`.

**Solution**: Use `re.search()` with a non-greedy pattern.

```python
# ✅ CORRECT - Finds a link anywhere in the string
import re
match = re.search(r"\[(.*?)\]\((.*?)\)", text_with_link)
if match:
    link_text = match.group(1)
    link_url = match.group(2)
```

#### Empty State Handling

**Issue**: Renderers may fail or produce blank pages when data is missing.

**Solution**: Always check for empty data and render a user-friendly message.

```python
if not data.get("items"):
    container.append("<div class='empty-state'><p>No data available for this report.</p></div>")
```

## 2. Information Retrieval Strategy

The project prioritizes **data freshness** over a static knowledge base. Instead of a traditional RAG that can become stale, agents use a suite of real-time tools to fetch information on demand.

### 2.1. Core Principle: Real-Time Retrieval

Financial markets are highly dynamic. To provide accurate and timely analysis, agents retrieve live data from the web for every task.

### 2.2. Key Retrieval Tools

- **`SerperDevTool` / `TavilyTool`**: For broad, general-purpose web searches to gather initial information.
- **ScraperFactory-selected scraper (`get_scraper()`)**: Centralized website scraping; defaults to `ScrapeNinjaTool`. Override via `WEB_SCRAPER_PROVIDER` (`scrapeninja`, `firecrawl`). Direct Firecrawl usage is deprecated in crews.
- **`YahooFinanceNewsTool`**: For fetching the latest financial news for a specific ticker, providing timely market-moving information.

### 2.3. Why Not a Traditional RAG?

- **Data Staleness**: A vector database would require constant, resource-intensive updates.
- **Scope Limitation**: A pre-populated database is limited, whereas live tools can access the entire public web.

The `SaveToRagTool` is used not as a permanent knowledge base, but as a **short-term memory or "scratchpad"** for agents to share information within a single crew execution.

## 3. Case Study: Refactoring the Sales Prospecting Report

The evolution of the `SalesProspectingReport` provides a clear example of applying architectural principles to solve real-world data challenges.

### 3.1. The Initial Problem

The first version of the `SalesProspectingReport` relied on a highly complex, nested Pydantic model called `StructuredDataReport`. This model was designed to capture a wide array of metrics, KPIs, data series, and tables.

**Challenge**: The data generated by the LLM agents did not align with this rigid and complex structure. The output was a simple, flat JSON with fields like `company_overview` and `key_contacts`. As a result, the Pydantic validation failed, and the rendering process broke.

### 3.2. The Solution: Data-Centric Refactoring

Instead of forcing the agents to conform to an overly complex model, the architecture was adapted to the data.

1. **Model Simplification**: The `SalesProspectingReport` Pydantic model was completely redesigned to match the actual data being produced. The dependency on `StructuredDataReport` was removed, and a new, simpler structure was implemented:
    - `company_overview: str`
    - `key_contacts: List[KeyContact]` (with a new `KeyContact` sub-model)
    - `approach_strategy: str`
    - `remaining_information: str`

2. **Renderer and Factory Update**: The `SalesProspectingRenderer` and `sales_prospecting_html_factory` were rewritten to work with the new, simpler model. This involved:
    - Removing the logic for rendering metrics and KPIs.
    - Adding new sections for `company_overview`, `key_contacts`, and `remaining_information`.
    - Updating the CSS to create a modern, professional layout with cards for key contacts.

3. **Data File Correction**: The `debug/repair_attempt...json` file was updated to conform to the new, simpler Pydantic model, ensuring that tests and local development would work correctly.

### 3.3. Architectural Lessons

- **Model the Data You Have**: Design Pydantic models that reflect the actual data being generated, not an idealized version.
- **Simplicity Over Complexity**: A simpler, flatter data structure is often more robust and easier to work with than a deeply nested one.
- **Decouple Rendering from Data Structure**: While the renderer needs to understand the data, the refactoring was made easier because the rendering logic was contained within the `SalesProspectingRenderer` and not scattered across the application.
