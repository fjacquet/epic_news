# HTML Rendering System Architecture

**Audience:** Developers creating crews with HTML output
**Scope:** Complete guide to epic_news rendering system
**Related Docs:** [CLAUDE.md](../../CLAUDE.md), [Tutorial: Creating Your First Crew](../tutorials/01_YOUR_FIRST_CREW.md)

## Overview

The epic_news project uses a **deterministic Python rendering system** to transform structured Pydantic data into HTML reports. This architecture ensures:

- **Separation of concerns**: Crew logic separate from presentation
- **Type safety**: Pydantic validation before rendering
- **Dark mode support**: CSS variables with automatic theme switching
- **Consistency**: All reports share universal template structure
- **Extensibility**: Easy to add new renderers

The system consists of four main components:

1. **TemplateManager**: Central orchestrator
2. **BaseRenderer**: Abstract interface for all renderers
3. **Specialized Renderers**: Crew-specific HTML generators (16 implementations)
4. **RendererFactory**: Dynamic renderer instantiation

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                     ReceptionFlow                        │
│                  (main.py @listen)                       │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ 1. Execute crew with inputs
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   CrewAI Crew                            │
│           (e.g., PoemCrew, CookingCrew)                  │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ 2. Return CrewOutput with JSON
                       ▼
┌──────────────────────────────────────────────────────────┐
│              Pydantic Model Validation                   │
│     (e.g., PoemJSONOutput, RecipeReport)                 │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ 3. Pass validated model_dump()
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   TemplateManager                        │
│          render_report(crew_type, data)                  │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ 4. Delegate to renderer
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  RendererFactory                         │
│         create_renderer(crew_type)                       │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ 5. Return specialized renderer
                       ▼
┌──────────────────────────────────────────────────────────┐
│              Specialized Renderer                        │
│    (PoemRenderer, CookingRenderer, etc.)                 │
│                render(data) -> HTML                      │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ 6. Generate HTML body
                       ▼
┌──────────────────────────────────────────────────────────┐
│              Universal Template                          │
│    (templates/universal_report_template.html)            │
│  {{ report_title }}, {{ report_body }}, etc.             │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ 7. Final HTML report
                       ▼
                ┌──────────────┐
                │  Output File │
                │  (.html)     │
                └──────────────┘
```

## Component Details

### 1. TemplateManager

**Location:** `src/epic_news/utils/html/template_manager.py`

**Responsibilities:**
- Load universal HTML template
- Generate contextual titles (e.g., "🌌 Création Poétique")
- Delegate body generation to specialized renderers
- Replace template placeholders with actual content
- Handle rendering errors gracefully

**Key Methods:**

```python
class TemplateManager:
    def render_report(self, selected_crew: str, content_data: dict[str, Any]) -> str:
        """Main method to render a complete HTML report."""
        # 1. Load universal template
        template_html = self.load_template("universal_report_template.html")

        # 2. Generate contextual title
        title = self.generate_contextual_title(selected_crew, content_data)

        # 3. Generate body using specialized renderer
        body_content = self.generate_contextual_body(content_data, selected_crew)

        # 4. Replace placeholders
        html_content = template_html.replace("{{ report_title }}", title)
        html_content = html_content.replace("{{ report_body|safe }}", body_content)
        html_content = html_content.replace("{{ generation_date }}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return html_content

    def generate_contextual_body(self, content_data: dict[str, Any], selected_crew: str) -> str:
        """Delegate to specialized renderer via RendererFactory."""
        if RendererFactory.has_specialized_renderer(selected_crew):
            renderer = RendererFactory.create_renderer(selected_crew)
            return renderer.render(content_data)

        # Fallback to generic renderer
        renderer = RendererFactory.create_renderer("GENERIC")
        return renderer.render(content_data, selected_crew)
```

**Usage Example:**

```python
from epic_news.utils.html.template_manager import TemplateManager

template_manager = TemplateManager()
html_content = template_manager.render_report(
    selected_crew="POEM",
    content_data={
        "title": "Ode to Python",
        "poem": "Lines of code, elegant and bright...",
        "theme": "Technology"
    }
)

Path("output/poem.html").write_text(html_content, encoding="utf-8")
```

### 2. BaseRenderer

**Location:** `src/epic_news/utils/html/template_renderers/base_renderer.py`

**Purpose:** Abstract interface that all specialized renderers must implement.

**Interface:**

```python
from abc import ABC, abstractmethod
from typing import Any
from bs4 import BeautifulSoup

class BaseRenderer(ABC):
    """Abstract base class for all HTML content renderers."""

    @abstractmethod
    def __init__(self):
        """Initialize the renderer."""
        pass

    @abstractmethod
    def render(self, data: dict[str, Any]) -> str:
        """
        Render content data to HTML string.

        Args:
            data: Dictionary containing content data

        Returns:
            HTML string for the content body
        """
        pass

    # Helper methods available to all renderers:

    def create_soup(self, tag: str = "div", **attrs) -> BeautifulSoup:
        """Create a new BeautifulSoup object with a root element."""

    def add_section(self, soup: BeautifulSoup, parent_selector: str,
                    tag: str, content: str = "", **attrs) -> None:
        """Add a new section to the soup."""

    def escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
```

**Key Features:**
- All renderers use **BeautifulSoup** for structured HTML generation
- Helper methods reduce boilerplate
- Enforces consistent rendering interface

### 3. RendererFactory

**Location:** `src/epic_news/utils/html/template_renderers/renderer_factory.py`

**Purpose:** Dynamic instantiation of specialized renderers based on crew type.

**Implementation:**

```python
class RendererFactory:
    """Factory for creating crew-specific HTML renderers."""

    _RENDERER_MAP: dict[str, type[BaseRenderer]] = {
        "BOOK_SUMMARY": BookSummaryRenderer,
        "COOKING": CookingRenderer,
        "DEEPRESEARCH": DeepResearchRenderer,
        "FINDAILY": FinancialRenderer,
        "GENERIC": GenericRenderer,
        "HOLIDAY_PLANNER": HolidayRenderer,
        "MEETING_PREP": MeetingPrepRenderer,
        "MENU": MenuRenderer,
        "NEWSDAILY": NewsDailyRenderer,
        "POEM": PoemRenderer,
        "RSS_WEEKLY": RssWeeklyRenderer,
        "SAINT": SaintRenderer,
        "SHOPPING": ShoppingRenderer,
        "COMPANY_NEWS": CompanyNewsRenderer,
        "CROSS_REFERENCE_REPORT": CrossReferenceReportRenderer,
        "SALESPROSPECTING": SalesProspectingRenderer,
    }

    @classmethod
    def create_renderer(cls, crew_type: str) -> BaseRenderer:
        """Create appropriate renderer for the given crew type."""
        renderer_class = cls._RENDERER_MAP.get(crew_type, GenericRenderer)
        return renderer_class()

    @classmethod
    def has_specialized_renderer(cls, crew_type: str) -> bool:
        """Check if a crew type has a specialized renderer."""
        return crew_type in cls._RENDERER_MAP

    @classmethod
    def register_renderer(cls, crew_type: str, renderer_class: type[BaseRenderer]) -> None:
        """Register a new renderer for a crew type."""
        cls._RENDERER_MAP[crew_type] = renderer_class
```

**Supported Renderers (16 total):**

| Crew Type | Renderer Class | Description |
|-----------|----------------|-------------|
| `BOOK_SUMMARY` | `BookSummaryRenderer` | Book analysis with chapters, themes |
| `COMPANY_NEWS` | `CompanyNewsRenderer` | Company news with sentiment analysis |
| `COOKING` | `CookingRenderer` | Recipe with ingredients, instructions |
| `CROSS_REFERENCE_REPORT` | `CrossReferenceReportRenderer` | Multi-source analysis |
| `DEEPRESEARCH` | `DeepResearchRenderer` | Comprehensive research reports |
| `FINDAILY` | `FinancialRenderer` | Financial data with tables, metrics |
| `GENERIC` | `GenericRenderer` | Fallback for any data structure |
| `HOLIDAY_PLANNER` | `HolidayRenderer` | Travel itinerary with activities |
| `MEETING_PREP` | `MeetingPrepRenderer` | Meeting agenda with topics |
| `MENU` | `MenuRenderer` | Weekly meal plan |
| `NEWSDAILY` | `NewsDailyRenderer` | Daily news by category |
| `POEM` | `PoemRenderer` | Poetry with verses, themes |
| `RSS_WEEKLY` | `RssWeeklyRenderer` | RSS feed aggregation |
| `SAINT` | `SaintRenderer` | Saint information with history |
| `SALESPROSPECTING` | `SalesProspectingRenderer` | Sales leads with contact info |
| `SHOPPING` | `ShoppingRenderer` | Product recommendations |

### 4. Specialized Renderers

Each renderer extends `BaseRenderer` and implements crew-specific HTML generation.

**Example: PoemRenderer** (`src/epic_news/utils/html/template_renderers/poem_renderer.py`)

```python
class PoemRenderer(BaseRenderer):
    """Renders poem content with artistic formatting."""

    def __init__(self):
        """Initialize the poem renderer."""
        super().__init__()

    def render(self, data: dict[str, Any]) -> str:
        """Render poem data to HTML."""
        # 1. Create main container
        soup = self.create_soup("div")
        container = soup.find("div")
        container.attrs["class"] = ["poem-report"]

        # 2. Add structured sections
        self._add_header(soup, container, data)
        self._add_poem_content(soup, container, data)
        self._add_analysis(soup, container, data)

        # 3. Add inline styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add poem header with title and theme."""
        header_div = soup.new_tag("div")
        header_div.attrs["class"] = ["poem-header"]

        title = data.get("title", "Poème")
        title_tag = soup.new_tag("h2")
        title_tag.string = f"🌌 {title}"
        header_div.append(title_tag)

        container.append(header_div)

    def _add_poem_content(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add poem verses."""
        # Handle verses array
        verses = data.get("verses", [])
        if verses:
            for verse in verses:
                # Create verse structure
                pass

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles with CSS variables."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .poem-report {
            max-width: 700px;
            margin: 0 auto;
        }
        .poem-header {
            background: var(--container-bg, #ffffff);
            border: 1px solid var(--border-color, #dee2e6);
            color: var(--heading-color, #212529);
        }
        """
        soup.append(style_tag)
```

## Complete Rendering Flow

### Step-by-Step Example: Poem Crew

**1. Execute Crew in ReceptionFlow**

```python
# In src/epic_news/main.py
@listen("generate_poem")
def generate_poem(self, message: str):
    result = PoemCrew().crew().kickoff(inputs={"subject": message})

    # Parse to Pydantic model
    poem_report = PoemJSONOutput.model_validate(json.loads(result.raw))

    # Render to HTML
    template_manager = TemplateManager()
    html_content = template_manager.render_report(
        selected_crew="POEM",
        content_data=poem_report.model_dump()
    )

    # Write file
    Path("output/poem/poem.html").write_text(html_content, encoding="utf-8")
```

**2. TemplateManager Orchestration**

```python
# TemplateManager.render_report() flow:
# 1. Load universal template from templates/universal_report_template.html
# 2. Generate title: "🌌 Création Poétique - {poem_title}"
# 3. Call generate_contextual_body() which delegates to RendererFactory
# 4. RendererFactory returns PoemRenderer instance
# 5. PoemRenderer.render() generates HTML body
# 6. Replace {{ report_title }} and {{ report_body }} placeholders
# 7. Return complete HTML document
```

**3. PoemRenderer HTML Generation**

```python
# PoemRenderer.render() flow:
# 1. Create BeautifulSoup with <div class="poem-report">
# 2. _add_header(): Add title, theme
# 3. _add_poem_content(): Add verses with line breaks
# 4. _add_analysis(): Add poetic analysis section
# 5. _add_styles(): Inject CSS with CSS variables
# 6. Return HTML string
```

**4. Final HTML Structure**

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>🌌 Création Poétique - Ode to Python</title>
    <!-- CSS from universal template -->
    <style>
        /* Dark mode variables */
        :root {
            --container-bg: #ffffff;
            --text-color: #212529;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --container-bg: #1e1e1e;
                --text-color: #e0e0e0;
            }
        }
    </style>
</head>
<body>
    <div class="poem-report">
        <!-- Content from PoemRenderer -->
        <div class="poem-header">
            <h2>🌌 Ode to Python</h2>
        </div>
        <div class="poem-content">
            <!-- Verses -->
        </div>
    </div>
    <!-- Inline styles from PoemRenderer -->
    <style>
        .poem-report { max-width: 700px; }
        .poem-header { background: var(--container-bg, #ffffff); }
    </style>
</body>
</html>
```

## Creating a New Renderer

Follow these steps to add a new renderer for your crew:

### Step 1: Create Renderer Class

Create `src/epic_news/utils/html/template_renderers/my_crew_renderer.py`:

```python
"""
My Crew Renderer

Renders my crew data to structured HTML using BeautifulSoup.
"""

from typing import Any
from bs4 import BeautifulSoup
from .base_renderer import BaseRenderer


class MyCrewRenderer(BaseRenderer):
    """Renders my crew reports."""

    def __init__(self):
        """Initialize the renderer."""
        super().__init__()  # CRITICAL: Always call super().__init__()

    def render(self, data: dict[str, Any]) -> str:
        """
        Render data to HTML.

        Args:
            data: Dictionary containing crew output data

        Returns:
            HTML string for the report body
        """
        # 1. Create main container
        soup = self.create_soup("div")
        container = soup.find("div")
        container.attrs["class"] = ["my-crew-report"]  # Use attrs["class"], NOT class_

        # 2. Add structured sections
        self._add_header(soup, container, data)
        self._add_content(soup, container, data)
        self._add_footer(soup, container, data)

        # 3. Add inline styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add report header."""
        header = soup.new_tag("div")
        header.attrs["class"] = ["report-header"]

        title = data.get("title", "My Crew Report")
        h2 = soup.new_tag("h2")
        h2.string = f"🚀 {title}"
        header.append(h2)

        container.append(header)

    def _add_content(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add main content."""
        # Handle empty state
        items = data.get("items", [])
        if not items:
            empty_p = soup.new_tag("p")
            empty_p.string = "No items found."
            container.append(empty_p)
            return

        # Render items
        for item in items:
            item_div = soup.new_tag("div")
            item_div.attrs["class"] = ["item-card"]
            item_div.string = str(item)
            container.append(item_div)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles using CSS variables with fallbacks."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .my-crew-report {
            max-width: 900px;
            margin: 0 auto;
        }
        .report-header {
            background: var(--container-bg, #ffffff);
            border: 1px solid var(--border-color, #dee2e6);
            padding: 2rem;
            border-radius: 12px;
        }
        .report-header h2 {
            color: var(--heading-color, #212529);
            margin: 0;
        }
        .item-card {
            background: var(--container-bg, #ffffff);
            border: 1px solid var(--border-color, #dee2e6);
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 8px;
        }
        """
        soup.append(style_tag)
```

### Step 2: Register in RendererFactory

Edit `src/epic_news/utils/html/template_renderers/renderer_factory.py`:

```python
from .my_crew_renderer import MyCrewRenderer

class RendererFactory:
    _RENDERER_MAP: dict[str, type[BaseRenderer]] = {
        # ... existing renderers ...
        "MY_CREW": MyCrewRenderer,  # Add your renderer
    }
```

### Step 3: Update __init__.py

Edit `src/epic_news/utils/html/template_renderers/__init__.py`:

```python
from .my_crew_renderer import MyCrewRenderer

__all__ = [
    # ... existing exports ...
    "MyCrewRenderer",
]
```

### Step 4: Use in ReceptionFlow

In `src/epic_news/main.py`:

```python
@listen("generate_my_crew_report")
def generate_my_crew_report(self, message: str):
    result = MyCrewCrew().crew().kickoff(inputs={"topic": message})

    report = MyCrewReport.model_validate(json.loads(result.raw))

    template_manager = TemplateManager()
    html_content = template_manager.render_report(
        selected_crew="MY_CREW",  # Must match RendererFactory key
        content_data=report.model_dump()
    )

    Path("output/my_crew/report.html").write_text(html_content, encoding="utf-8")
```

## Best Practices

### 1. CSS Variables with Fallbacks

Always use CSS variables with fallback values for dark mode support:

```css
/* ✅ CORRECT - Works in light and dark mode */
color: var(--text-color, #495057);
background: var(--container-bg, #ffffff);
border: 1px solid var(--border-color, #dee2e6);

/* ❌ WRONG - Hard-coded colors break dark mode */
color: #495057;
background: #ffffff;
```

**Available CSS Variables:**

| Variable | Light Mode | Dark Mode | Usage |
|----------|------------|-----------|-------|
| `--container-bg` | `#ffffff` | `#1e1e1e` | Card backgrounds |
| `--text-color` | `#495057` | `#e0e0e0` | Body text |
| `--heading-color` | `#212529` | `#ffffff` | Headings |
| `--border-color` | `#dee2e6` | `#444444` | Borders |
| `--link-color` | `#007bff` | `#4dabf7` | Links |
| `--accent-color` | `#ffc107` | `#ffd43b` | Highlights |

### 2. Use attrs["class"] Pattern

BeautifulSoup has a bug with the `class_` keyword. Always use `attrs["class"]`:

```python
# ✅ CORRECT - Sets class attribute properly
container.attrs["class"] = ["my-class", "another-class"]

# ❌ WRONG - May not work correctly
container["class_"] = "my-class"
```

### 3. Always Implement __init__

Even if your renderer has no special initialization, implement `__init__`:

```python
# ✅ CORRECT
class MyRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

# ❌ WRONG - Missing __init__ causes errors
class MyRenderer(BaseRenderer):
    def render(self, data):
        pass
```

### 4. Handle Empty States Gracefully

Always check for empty/missing data and provide fallback content:

```python
def _add_items(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
    items = data.get("items", [])

    # ✅ CORRECT - Handle empty state
    if not items:
        empty_p = soup.new_tag("p")
        empty_p.string = "No items available."
        container.append(empty_p)
        return

    # Render items
    for item in items:
        # ...
```

### 5. Structure Methods Logically

Break rendering into logical private methods:

```python
def render(self, data: dict[str, Any]) -> str:
    soup = self.create_soup("div")
    container = soup.find("div")

    # Clear, logical progression
    self._add_header(soup, container, data)
    self._add_summary(soup, container, data)
    self._add_main_content(soup, container, data)
    self._add_footer(soup, container, data)
    self._add_styles(soup)

    return str(soup)
```

### 6. Use Semantic HTML

Use appropriate HTML5 semantic tags:

```python
# ✅ CORRECT - Semantic structure
header = soup.new_tag("header")
article = soup.new_tag("article")
section = soup.new_tag("section")
footer = soup.new_tag("footer")

# ❌ WRONG - Everything as divs
header = soup.new_tag("div")
header.attrs["class"] = ["header"]
```

### 7. Escape User Content

Always escape user-provided text to prevent XSS:

```python
# ✅ CORRECT - Escaped via .string assignment
title_tag = soup.new_tag("h2")
title_tag.string = user_input  # Automatically escaped

# Use BaseRenderer.escape_html() for manual escaping
escaped = self.escape_html(user_input)
```

## Common Pitfalls

### Pitfall 1: class_ Attribute Bug

**Problem:** Using `class_="my-class"` in BeautifulSoup doesn't work reliably.

**Solution:**
```python
# ✅ CORRECT
tag.attrs["class"] = ["my-class"]

# ❌ WRONG
tag["class_"] = "my-class"
```

### Pitfall 2: Hard-coded Colors

**Problem:** Hard-coded colors break dark mode.

**Solution:**
```python
# ✅ CORRECT - CSS variable with fallback
style = "color: var(--text-color, #495057);"

# ❌ WRONG - Hard-coded
style = "color: #495057;"
```

### Pitfall 3: Missing __init__ Method

**Problem:** Renderer instantiation fails without `__init__`.

**Solution:**
```python
# ✅ CORRECT
def __init__(self):
    super().__init__()
```

### Pitfall 4: Not Handling Empty Data

**Problem:** Renderer crashes or shows broken HTML when data is missing.

**Solution:**
```python
# ✅ CORRECT - Check and provide fallback
items = data.get("items", [])
if not items:
    show_empty_state()
    return
```

### Pitfall 5: Renderer Not Registered

**Problem:** `RendererFactory.create_renderer("MY_CREW")` returns `GenericRenderer`.

**Solution:** Add your renderer to `RendererFactory._RENDERER_MAP`:
```python
_RENDERER_MAP = {
    # ...
    "MY_CREW": MyCrewRenderer,
}
```

### Pitfall 6: Forgetting to Import Renderer

**Problem:** `ImportError: cannot import name 'MyCrewRenderer'`

**Solution:** Import renderer in `renderer_factory.py`:
```python
from .my_crew_renderer import MyCrewRenderer
```

## Universal Template Structure

**Location:** `templates/universal_report_template.html`

The universal template provides the outer HTML structure:

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>

    <!-- Dark mode CSS variables -->
    <style>
        :root {
            --container-bg: #ffffff;
            --text-color: #212529;
            --heading-color: #212529;
            --border-color: #dee2e6;
            --link-color: #007bff;
            --accent-color: #ffc107;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --container-bg: #1e1e1e;
                --text-color: #e0e0e0;
                --heading-color: #ffffff;
                --border-color: #444444;
                --link-color: #4dabf7;
                --accent-color: #ffd43b;
            }
        }

        body {
            background: var(--container-bg);
            color: var(--text-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 2rem;
            transition: background-color 0.3s, color 0.3s;
        }
    </style>
</head>
<body>
    {{ report_body|safe }}

    <footer style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border-color);">
        <p style="color: var(--text-color); font-size: 0.9rem;">
            Generated on {{ generation_date }}
        </p>
    </footer>
</body>
</html>
```

**Placeholders:**
- `{{ report_title }}`: Contextual title from `generate_contextual_title()`
- `{{ report_body|safe }}`: HTML body from specialized renderer
- `{{ generation_date }}`: Current timestamp

## Testing Renderers

### Unit Test Example

```python
"""Test for My Crew Renderer."""

import pytest
from epic_news.utils.html.template_renderers.my_crew_renderer import MyCrewRenderer


def test_renderer_initialization():
    """Test that renderer can be instantiated."""
    renderer = MyCrewRenderer()
    assert renderer is not None


def test_render_with_valid_data():
    """Test rendering with valid data."""
    renderer = MyCrewRenderer()

    test_data = {
        "title": "Test Report",
        "items": [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200},
        ]
    }

    html = renderer.render(test_data)

    # Assertions
    assert "<div" in html
    assert "Test Report" in html
    assert "Item 1" in html
    assert "class=\"my-crew-report\"" in html or 'class="my-crew-report"' in html


def test_render_with_empty_data():
    """Test rendering handles empty data gracefully."""
    renderer = MyCrewRenderer()

    test_data = {"title": "Empty Report", "items": []}

    html = renderer.render(test_data)

    assert "No items available" in html or "No items found" in html


def test_css_variables_usage():
    """Test that CSS uses variables with fallbacks."""
    renderer = MyCrewRenderer()

    html = renderer.render({"title": "Test"})

    # Check for CSS variable usage
    assert "var(--" in html
    assert "--container-bg" in html or "--text-color" in html
```

### Integration Test Example

```python
"""Integration test for rendering system."""

from epic_news.utils.html.template_manager import TemplateManager


def test_full_rendering_pipeline():
    """Test complete rendering pipeline."""
    template_manager = TemplateManager()

    test_data = {
        "title": "Integration Test",
        "items": [{"name": "Test Item"}]
    }

    html = template_manager.render_report(
        selected_crew="MY_CREW",
        content_data=test_data
    )

    # Check template structure
    assert "<!DOCTYPE html>" in html
    assert "<html lang=\"fr\">" in html
    assert "Test Item" in html
    assert "Generated on" in html
```

## Debugging Tips

### 1. Check Renderer Registration

```python
from epic_news.utils.html.template_renderers.renderer_factory import RendererFactory

# List all registered renderers
print(RendererFactory.get_supported_crew_types())

# Check if your renderer is registered
print(RendererFactory.has_specialized_renderer("MY_CREW"))
```

### 2. Inspect Generated HTML

```python
# Pretty-print HTML for debugging
from bs4 import BeautifulSoup

html = renderer.render(data)
soup = BeautifulSoup(html, "html.parser")
print(soup.prettify())
```

### 3. Test Renderer in Isolation

```python
# Test renderer without full pipeline
from epic_news.utils.html.template_renderers.my_crew_renderer import MyCrewRenderer

renderer = MyCrewRenderer()
test_data = {"title": "Debug Test"}
html = renderer.render(test_data)
print(html)
```

### 4. Validate CSS Variables

```bash
# Check for CSS variable usage in your renderer
grep -r "var(--" src/epic_news/utils/html/template_renderers/my_crew_renderer.py
```

## Summary

The epic_news rendering system provides:

✅ **Modular architecture** - Easy to extend with new renderers
✅ **Type safety** - Pydantic validation before rendering
✅ **Dark mode support** - CSS variables with automatic theming
✅ **Consistent structure** - Universal template for all reports
✅ **Maintainability** - Clear separation of concerns

**Key Points:**
- TemplateManager orchestrates rendering
- RendererFactory dynamically instantiates specialized renderers
- All renderers extend BaseRenderer and use BeautifulSoup
- Use CSS variables with fallbacks for dark mode
- Use `attrs["class"]` pattern, not `class_`
- Always implement `__init__` and handle empty states

## Related Documentation

- [Tutorial: Creating Your First Crew](../tutorials/01_YOUR_FIRST_CREW.md) - Complete crew creation guide
- [CLAUDE.md](../../CLAUDE.md) - Architectural patterns and project standards
- [COMMON_ERRORS.md](../troubleshooting/COMMON_ERRORS.md) - HTML rendering troubleshooting

## Need Help?

- Review existing renderers in `src/epic_news/utils/html/template_renderers/`
- Check `RendererFactory` for registration examples
- Examine `TemplateManager` for orchestration flow
- Test your renderer with unit tests before integration

---

**You now have a complete understanding of the epic_news HTML rendering system!**
