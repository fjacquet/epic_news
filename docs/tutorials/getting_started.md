# Tutorial: Creating Your First Crew

**Target Audience:** Developers new to epic_news
**Time Estimate:** 1-2 hours
**Prerequisites:** Python 3.13+, `uv` package manager, basic CrewAI concepts
**Related Docs:** [CLAUDE.md](../../CLAUDE.md), [COMMON_ERRORS.md](../troubleshooting/COMMON_ERRORS.md)

## What You'll Build

In this tutorial, you'll create a complete **Book Recommendation Crew** from scratch. This crew will:

- Take a genre as input (e.g., "science fiction", "mystery")
- Research top 5 books in that genre
- Generate a structured HTML report with book summaries, ratings, and purchase links
- Follow all epic_news architectural patterns

By the end, you'll understand:
- The two-agent pattern (researcher + reporter)
- How to define agents and tasks in YAML
- How to create Pydantic models with legacy syntax
- How to build HTML renderers using BeautifulSoup
- How to integrate with ReceptionFlow

## Project Structure Overview

The epic_news project uses a standardized structure for all crews:

```
src/epic_news/crews/
└── book_recommender/
    ├── __init__.py
    ├── book_recommender_crew.py    # Python implementation
    └── config/
        ├── agents.yaml              # Agent definitions
        └── tasks.yaml               # Task definitions
```

Additional files you'll create:
- `src/epic_news/models/crews/book_recommendation_report.py` - Pydantic model
- `src/epic_news/utils/html/template_renderers/book_recommender_renderer.py` - HTML renderer

## Step 1: Create Directory Structure

First, create the crew directory and configuration files:

```bash
cd src/epic_news/crews
mkdir -p book_recommender/config
cd book_recommender
touch __init__.py book_recommender_crew.py
touch config/agents.yaml config/tasks.yaml
```

## Step 2: Define Agents in YAML

Edit `config/agents.yaml` to define two agents following the **researcher + reporter pattern**:

```yaml
---
researcher:
  role: Senior Book Research Specialist
  goal: >
    Find and analyze the top 5 books in the {genre} genre based on critical
    acclaim, reader reviews, and literary significance. Gather comprehensive
    information including titles, authors, publication dates, ratings, and summaries.
  backstory: >
    You are a literary expert with 20+ years of experience in book curation.
    You have extensive knowledge of various genres and can identify truly
    exceptional works. You excel at finding reliable sources and distinguishing
    quality literature from popular trends.

reporter:
  role: Lead Book Report Analyst
  goal: >
    Transform research findings into a perfectly structured JSON report that
    conforms exactly to the BookRecommendationReport Pydantic model.
    CRITICAL: Your output MUST be valid JSON with proper escaping of all special characters.
  backstory: >
    You are a meticulous data analyst and JSON expert. You transform raw research
    into clean, structured reports. Your JSON outputs are always syntactically
    correct and conform exactly to specified schemas. You never include explanatory
    text outside the JSON structure.
```

**Key points:**
- `researcher` agent has detailed backstory for quality research
- `reporter` agent emphasizes JSON correctness (see [JSON Escaping errors](../troubleshooting/COMMON_ERRORS.md#json-escaping-errors))
- Both use placeholders like `{genre}` for dynamic inputs

## Step 3: Define Tasks in YAML

Edit `config/tasks.yaml` to define research and reporting tasks:

```yaml
---
research_task:
  description: >
    Research the top 5 books in the {genre} genre. For each book:
    1. Identify the title, author, and publication year
    2. Find the average rating from multiple sources (Goodreads, Amazon, etc.)
    3. Gather a comprehensive summary (200+ words)
    4. Note key themes, writing style, and target audience
    5. Collect purchase links from major retailers

    Use web search tools to find authoritative sources like literary reviews,
    bestseller lists, and book databases. Prioritize critically acclaimed works
    over purely commercial successes.
  expected_output: >
    A detailed markdown report with comprehensive information on 5 books,
    including titles, authors, ratings, summaries, themes, and purchase links.
  agent: researcher

reporting_task:
  description: |
    CRITICAL: Compile the book research into a single valid JSON object
    that strictly conforms to the BookRecommendationReport Pydantic model.

    REQUIRED STRUCTURE:
    - genre (string): The genre researched
    - generation_date (string): ISO 8601 date
    - books (array): Array of 5 book objects, each with:
      * title (string)
      * author (string)
      * publication_year (int)
      * rating (float): 0.0 to 5.0
      * summary (string): 200+ words
      * themes (array of strings)
      * purchase_links (array of objects with 'retailer' and 'url')

    JSON FORMATTING RULES:
    - Output ONLY valid JSON, no markdown, no explanations
    - Escape all special characters (quotes, apostrophes, backslashes)
    - Use double quotes for all strings
    - Ensure proper comma separation
    - Validate structure before output
  expected_output: |
    A valid JSON object matching BookRecommendationReport schema.
    Must be syntactically correct and directly parseable by json.loads().
  agent: reporter
  context: [research_task]
```

**Key points:**
- `research_task` has no `output_file` (passes data via context)
- `reporting_task` has explicit JSON formatting rules
- Tasks reference agents by name

## Step 4: Create Pydantic Model (Legacy Syntax)

Create `src/epic_news/models/crews/book_recommendation_report.py`:

```python
from typing import Optional

from pydantic import BaseModel, Field


class PurchaseLink(BaseModel):
    """Purchase link for a book."""

    retailer: str = Field(..., description="Retailer name (e.g., Amazon, Barnes & Noble)")
    url: str = Field(..., description="Purchase URL")


class BookDetail(BaseModel):
    """Detailed information about a single book."""

    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Author name")
    publication_year: int = Field(..., description="Year published")
    rating: float = Field(..., description="Average rating (0.0 to 5.0)")
    summary: str = Field(..., description="Book summary (200+ words)")
    themes: list[str] = Field(default_factory=list, description="Key themes")
    purchase_links: list[PurchaseLink] = Field(default_factory=list, description="Purchase links")


class BookRecommendationReport(BaseModel):
    """Complete book recommendation report for a genre."""

    genre: str = Field(..., description="Genre researched")
    generation_date: str = Field(..., description="Report generation date (ISO 8601)")
    books: list[BookDetail] = Field(..., description="List of 5 recommended books")
    summary: Optional[str] = Field(None, description="Overall genre summary")


```

**CRITICAL SYNTAX NOTES:**

✅ **CORRECT** - Use `Optional[str]` for optional fields:
```python
summary: Optional[str] = Field(None, description="...")
```

❌ **WRONG** - Do NOT use Python 3.10+ Union syntax:
```python
summary: str | None = Field(None, description="...")  # CAUSES AttributeError
```

**Why?** CrewAI's schema parser cannot handle `X | Y` syntax. Always use `Union[X, Y]` or `Optional[X]`. See [Pydantic Validation Errors](../troubleshooting/COMMON_ERRORS.md#pydantic-validation-errors) for details.

## Step 5: Implement Crew Class

Create `book_recommender_crew.py`:

```python
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.book_recommendation_report import BookRecommendationReport
from epic_news.tools.web_tools import get_search_tools, get_scrape_tools

load_dotenv()


@CrewBase
class BookRecommenderCrew:
    """
    Book Recommender crew for finding top books in a genre.
    Uses two-agent pattern: researcher (with tools) + reporter (no tools).
    """

    def __init__(self):
        # Resolve absolute paths to config files
        base_dir = Path(__file__).parent
        self.agents_config = str(base_dir / "config/agents.yaml")
        self.tasks_config = str(base_dir / "config/tasks.yaml")

    @agent
    def researcher(self) -> Agent:
        """Research agent with search and scraping tools."""
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
            tools=get_search_tools() + get_scrape_tools(),  # Tools assigned in code, NOT YAML
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            respect_context_window=True,
        )

    @agent
    def reporter(self) -> Agent:
        """Reporting agent with NO tools for clean JSON output."""
        return Agent(
            config=self.agents_config["reporter"],
            verbose=True,
            tools=[],  # NO TOOLS = No action traces in output
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            respect_context_window=True,
            system_template="""You are a JSON formatting expert.

            CRITICAL JSON FORMATTING RULES:
            - Output ONLY valid JSON, no explanations or markdown
            - Escape all special characters:
              * Use \\" for quotes inside strings
              * Use \\\\ for backslashes
              * French/special chars: "l'amour" → "l\\'amour"
            - Validate JSON syntax before output
            - Never include code blocks or extra text

            Your output must be directly parseable by json.loads().""",
        )

    @task
    def research_task(self) -> Task:
        """Research task - no output_file, passes data via context."""
        return Task(
            config=self.tasks_config["research_task"],
            agent=self.researcher(),
            async_execution=False,
        )

    @task
    def reporting_task(self) -> Task:
        """Reporting task - receives context from research_task."""
        return Task(
            config=self.tasks_config["reporting_task"],
            agent=self.reporter(),
            context=[self.research_task()],  # Receives research_task output
            output_pydantic=BookRecommendationReport,  # Validates against model
        )

    @crew
    def crew(self) -> Crew:
        """Create crew with sequential process."""
        try:
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                llm_timeout=LLMConfig.get_timeout("default"),
                max_iter=LLMConfig.get_max_iter(),
                max_rpm=LLMConfig.get_max_rpm(),
                verbose=True,
            )
        except Exception as e:
            error_msg = f"Error creating BookRecommenderCrew: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
```

**Key patterns explained:**

1. **Tools in code, NOT YAML**:
   ```python
   tools=get_search_tools() + get_scrape_tools()  # ✅ CORRECT
   ```
   Never define tools in `agents.yaml` - causes `KeyError` exceptions.

2. **Two-Agent Pattern**:
   - `researcher`: Has tools, no `output_file`
   - `reporter`: NO tools, has `output_pydantic`
   - Prevents action traces in HTML output

3. **LLMConfig usage**:
   ```python
   llm=LLMConfig.get_openrouter_llm()  # ✅ CORRECT
   llm_timeout=LLMConfig.get_timeout("default")  # ✅ CORRECT
   ```
   Never hardcode model names or timeouts.

4. **system_template**: Explicit JSON formatting instructions prevent escaping errors

## Step 6: Create HTML Renderer

Create `src/epic_news/utils/html/template_renderers/book_recommender_renderer.py`:

```python
"""
Book Recommender Renderer

Renders book recommendation data to structured HTML using BeautifulSoup.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class BookRecommenderRenderer(BaseRenderer):
    """Renders book recommendation reports with structured formatting."""

    def __init__(self):
        """Initialize the book recommender renderer."""
        super().__init__()

    def render(self, data: dict[str, Any]) -> str:
        """
        Render book recommendation data to HTML.

        Args:
            data: Dictionary containing book recommendation data

        Returns:
            HTML string for book recommendation content
        """
        # Create main container
        soup = self.create_soup("div")
        container = soup.find("div")
        # Use attrs["class"] pattern, NOT class_="..."
        container.attrs["class"] = ["book-recommender-report"]

        # Add header
        self._add_header(soup, container, data)

        # Add books section
        self._add_books(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add report header with genre and summary."""
        header_div = soup.new_tag("div")
        header_div.attrs["class"] = ["report-header"]

        # Title
        genre = data.get("genre", "Books")
        title_tag = soup.new_tag("h2")
        title_tag.string = f"📚 Top {genre.title()} Books"
        header_div.append(title_tag)

        # Summary if available
        summary = data.get("summary")
        if summary:
            summary_p = soup.new_tag("p")
            summary_p.attrs["class"] = ["genre-summary"]
            summary_p.string = summary
            header_div.append(summary_p)

        container.append(header_div)

    def _add_books(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add books section with individual book cards."""
        books = data.get("books", [])
        if not books:
            no_books_p = soup.new_tag("p")
            no_books_p.string = "No books found."
            container.append(no_books_p)
            return

        books_div = soup.new_tag("div")
        books_div.attrs["class"] = ["books-container"]

        for i, book in enumerate(books, 1):
            book_card = self._create_book_card(soup, book, i)
            books_div.append(book_card)

        container.append(books_div)

    def _create_book_card(self, soup: BeautifulSoup, book: dict[str, Any], rank: int) -> Any:
        """Create individual book card."""
        card = soup.new_tag("div")
        card.attrs["class"] = ["book-card"]

        # Rank and title
        title_div = soup.new_tag("div")
        title_div.attrs["class"] = ["book-header"]

        rank_span = soup.new_tag("span")
        rank_span.attrs["class"] = ["book-rank"]
        rank_span.string = f"#{rank}"
        title_div.append(rank_span)

        title_h3 = soup.new_tag("h3")
        title_h3.string = book.get("title", "Unknown Title")
        title_div.append(title_h3)

        card.append(title_div)

        # Author and year
        author_p = soup.new_tag("p")
        author_p.attrs["class"] = ["book-author"]
        author_p.string = f"by {book.get('author', 'Unknown')} ({book.get('publication_year', 'N/A')})"
        card.append(author_p)

        # Rating
        rating = book.get("rating", 0)
        rating_div = soup.new_tag("div")
        rating_div.attrs["class"] = ["book-rating"]
        rating_div.string = f"⭐ {rating:.1f}/5.0"
        card.append(rating_div)

        # Summary
        summary = book.get("summary", "No summary available.")
        summary_p = soup.new_tag("p")
        summary_p.attrs["class"] = ["book-summary"]
        summary_p.string = summary
        card.append(summary_p)

        # Themes
        themes = book.get("themes", [])
        if themes:
            themes_div = soup.new_tag("div")
            themes_div.attrs["class"] = ["book-themes"]

            themes_label = soup.new_tag("strong")
            themes_label.string = "Themes: "
            themes_div.append(themes_label)

            themes_span = soup.new_tag("span")
            themes_span.string = ", ".join(themes)
            themes_div.append(themes_span)

            card.append(themes_div)

        # Purchase links
        purchase_links = book.get("purchase_links", [])
        if purchase_links:
            links_div = soup.new_tag("div")
            links_div.attrs["class"] = ["purchase-links"]

            links_label = soup.new_tag("strong")
            links_label.string = "Buy: "
            links_div.append(links_label)

            for link_data in purchase_links:
                link = soup.new_tag("a", href=link_data.get("url", "#"))
                link.attrs["target"] = "_blank"
                link.string = link_data.get("retailer", "Store")
                links_div.append(link)
                links_div.append(soup.new_string(" | "))

            card.append(links_div)

        return card

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles using CSS variables with fallbacks."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .book-recommender-report {
            max-width: 900px;
            margin: 0 auto;
        }
        .report-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--container-bg, #ffffff);
            border-radius: 12px;
            border: 1px solid var(--border-color, #dee2e6);
        }
        .report-header h2 {
            color: var(--heading-color, #212529);
            margin-bottom: 1rem;
        }
        .genre-summary {
            color: var(--text-color, #495057);
            line-height: 1.6;
        }
        .books-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        .book-card {
            background: var(--container-bg, #ffffff);
            border: 1px solid var(--border-color, #dee2e6);
            border-radius: 8px;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .book-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .book-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        .book-rank {
            background: var(--primary-color, #007bff);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        .book-card h3 {
            color: var(--heading-color, #212529);
            margin: 0;
            flex: 1;
        }
        .book-author {
            color: var(--text-color, #6c757d);
            font-style: italic;
            margin: 0.5rem 0;
        }
        .book-rating {
            color: var(--accent-color, #ffc107);
            font-size: 1.1rem;
            margin: 0.5rem 0;
        }
        .book-summary {
            color: var(--text-color, #495057);
            line-height: 1.6;
            margin: 1rem 0;
        }
        .book-themes {
            margin: 1rem 0;
            padding: 0.75rem;
            background: rgba(108, 117, 125, 0.1);
            border-radius: 6px;
        }
        .purchase-links {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color, #dee2e6);
        }
        .purchase-links a {
            color: var(--link-color, #007bff);
            text-decoration: none;
            margin-right: 0.5rem;
        }
        .purchase-links a:hover {
            text-decoration: underline;
        }
        """
        soup.append(style_tag)
```

**Critical renderer patterns:**

1. **Use `attrs["class"]` NOT `class_`**:
   ```python
   container.attrs["class"] = ["book-recommender-report"]  # ✅ CORRECT
   # NOT: container["class_"] = "..."  # ❌ WRONG - BeautifulSoup bug
   ```

2. **CSS variables with fallbacks**:
   ```css
   color: var(--text-color, #495057);  /* Falls back to #495057 if variable undefined */
   ```

3. **Always implement `__init__`**:
   ```python
   def __init__(self):
       super().__init()  # Required even if empty
   ```

4. **Handle empty states**:
   ```python
   if not books:
       # Show "No books found" message
   ```

## Step 7: Register Renderer in Factory

Edit `src/epic_news/utils/html/template_renderers/renderer_factory.py` to register your renderer:

```python
from .book_recommender_renderer import BookRecommenderRenderer

class RendererFactory:
    _renderers = {
        # ... existing renderers ...
        "BOOK_RECOMMENDER": BookRecommenderRenderer,
    }
```

## Step 8: Integrate with ReceptionFlow

Edit `src/epic_news/main.py` to add a method for your crew:

```python
from epic_news.crews.book_recommender.book_recommender_crew import BookRecommenderCrew
from epic_news.models.crews.book_recommendation_report import BookRecommendationReport

class ReceptionFlow(Flow):
    # ... existing code ...

    @listen("generate_book_recommendations")
    def generate_book_recommendations(self, message: str):
        """Generate book recommendations for a genre."""
        logger.info(f"📚 Generating book recommendations for: {message}")

        try:
            # Extract genre from message (or use the whole message)
            genre = message

            # Execute crew
            result = BookRecommenderCrew().crew().kickoff(
                inputs={"genre": genre}
            )

            # Parse to Pydantic model
            report = BookRecommendationReport.model_validate(
                json.loads(result.raw)
            )

            # Generate HTML
            html_file = f"output/book_recommender/{genre.replace(' ', '_')}.html"
            template_manager = TemplateManager()
            html_content = template_manager.render_report(
                selected_crew="BOOK_RECOMMENDER",
                content_data=report.model_dump()
            )

            # Write file
            Path(html_file).parent.mkdir(parents=True, exist_ok=True)
            Path(html_file).write_text(html_content, encoding="utf-8")

            logger.info(f"✅ Book recommendations saved to {html_file}")
            return report

        except Exception as e:
            logger.error(f"❌ Error generating book recommendations: {e}")
            raise
```

## Step 9: Test Your Crew

Run your crew using the CrewAI command:

```bash
# Make sure you're in the project root
cd /path/to/epic_news

# Run the crew via ReceptionFlow
crewai flow kickoff

# When prompted, trigger your crew by saying:
# "Generate book recommendations for science fiction"
```

**Expected output:**
1. Researcher agent searches for top sci-fi books
2. Reporter agent formats results as JSON
3. HTML report generated at `output/book_recommender/science_fiction.html`
4. Open the HTML file in a browser to see your formatted report

## Step 10: Write Structure Tests

Create `tests/crews/book_recommender/test_book_recommender_structure.py`:

```python
"""Structure tests for Book Recommender crew."""

from pathlib import Path

import pytest


def test_crew_directory_structure():
    """Test that crew directory structure exists."""
    base_dir = Path("src/epic_news/crews/book_recommender")

    assert base_dir.exists(), "Crew directory should exist"
    assert (base_dir / "__init__.py").exists(), "__init__.py should exist"
    assert (base_dir / "book_recommender_crew.py").exists(), "Crew file should exist"
    assert (base_dir / "config").exists(), "Config directory should exist"
    assert (base_dir / "config/agents.yaml").exists(), "agents.yaml should exist"
    assert (base_dir / "config/tasks.yaml").exists(), "tasks.yaml should exist"


def test_pydantic_model_exists():
    """Test that Pydantic model exists and is importable."""
    from epic_news.models.crews.book_recommendation_report import (
        BookRecommendationReport,
        BookDetail,
        PurchaseLink,
    )

    assert BookRecommendationReport is not None
    assert BookDetail is not None
    assert PurchaseLink is not None


def test_renderer_exists():
    """Test that renderer exists and is importable."""
    from epic_news.utils.html.template_renderers.book_recommender_renderer import (
        BookRecommenderRenderer,
    )

    renderer = BookRecommenderRenderer()
    assert renderer is not None


def test_crew_instantiation():
    """Test that crew can be instantiated."""
    from epic_news.crews.book_recommender.book_recommender_crew import (
        BookRecommenderCrew,
    )

    crew_instance = BookRecommenderCrew()
    assert crew_instance is not None
    assert crew_instance.crew() is not None


def test_renderer_output():
    """Test that renderer produces valid HTML."""
    from epic_news.utils.html.template_renderers.book_recommender_renderer import (
        BookRecommenderRenderer,
    )

    test_data = {
        "genre": "science fiction",
        "generation_date": "2024-01-15",
        "books": [
            {
                "title": "Test Book",
                "author": "Test Author",
                "publication_year": 2020,
                "rating": 4.5,
                "summary": "A test book summary.",
                "themes": ["space", "adventure"],
                "purchase_links": [
                    {"retailer": "Amazon", "url": "https://amazon.com"}
                ],
            }
        ],
    }

    renderer = BookRecommenderRenderer()
    html = renderer.render(test_data)

    assert "<div" in html, "Should contain HTML div tags"
    assert "Test Book" in html, "Should contain book title"
    assert "4.5" in html, "Should contain rating"
```

Run tests:
```bash
uv run pytest tests/crews/book_recommender/ -v
```

## Common Issues & Solutions

### Issue 1: JSON Escaping Errors

**Error:**
```
pydantic_core.ValidationError: Invalid JSON: invalid escape at line 3
```

**Solution:** Add `system_template` to reporter agent with explicit escaping rules. See [JSON Escaping Errors](../troubleshooting/COMMON_ERRORS.md#json-escaping-errors) for full details.

### Issue 2: Action Traces in HTML Output

**Error:** HTML file contains agent thinking/tool calls instead of clean report.

**Solution:** Use **two-agent pattern** - only the reporter agent should have no tools and `output_file`. See [HTML Rendering Issues](../troubleshooting/COMMON_ERRORS.md#html-rendering-issues).

### Issue 3: AttributeError with Union Types

**Error:**
```
AttributeError: 'UnionType' object has no attribute 'copy_with'
```

**Solution:** Use legacy Pydantic syntax (`Optional[X]` not `X | None`). See [Pydantic Validation Errors](../troubleshooting/COMMON_ERRORS.md#pydantic-validation-errors).

### Issue 4: KeyError for Tools

**Error:**
```
KeyError: 'tools'
```

**Solution:** Never define tools in YAML - assign them programmatically in the `@agent` method. See [Crew Execution Errors](../troubleshooting/COMMON_ERRORS.md#crew-execution-errors).

### Issue 5: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'epic_news'
```

**Solution:** Run `uv pip install -e .` for editable install. See [Import/Module Errors](../troubleshooting/COMMON_ERRORS.md#import-module-errors).

### Issue 6: Renderer Not Found

**Error:**
```
Renderer for BOOK_RECOMMENDER not found
```

**Solution:** Register renderer in `RendererFactory._renderers` dictionary.

## Key Takeaways

✅ **Always use the two-agent pattern** for HTML reports (researcher + reporter)
✅ **Assign tools in Python code**, never in YAML
✅ **Use legacy Pydantic syntax** (`Optional[X]` not `X | None`)
✅ **Add system_template** to reporter agents for JSON formatting
✅ **Use CSS variables with fallbacks** in renderers
✅ **Use `attrs["class"]`** not `class_` in BeautifulSoup
✅ **Always implement `__init__`** in renderer classes
✅ **Handle empty states** gracefully in renderers
✅ **Use `LLMConfig`** methods, never hardcode LLM settings
✅ **Write structure tests** to ensure crew integrity

## Next Steps

- **Tutorial 2:** Adding Custom Tools (Coming soon)
- **Tutorial 3:** Advanced HTML Rendering (Coming soon)
- **Reference:** [Rendering Architecture](../reference/RENDERING_ARCHITECTURE.md)
- **Reference:** [Tools Complete Reference](../reference/TOOLS_COMPLETE_REFERENCE.md)
- **How-to:** [Debugging Crew Failures](../how-to/DEBUG_CREW_FAILURES.md)

## Need Help?

- Check [COMMON_ERRORS.md](../troubleshooting/COMMON_ERRORS.md) for troubleshooting
- Review [CLAUDE.md](../../CLAUDE.md) for architectural patterns
- Examine existing crews in `src/epic_news/crews/` for examples
- Ask questions in the project repository

---

**Congratulations!** You've successfully created your first epic_news crew. You now understand the complete workflow from YAML configuration to HTML rendering.
