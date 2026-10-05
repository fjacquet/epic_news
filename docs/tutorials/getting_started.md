# Tutorial: Creating Your First Crew

**Target Audience:** Developers new to epic_news
**Time Estimate:** 1-2 hours
**Prerequisites:** Python 3.13+, `uv` package manager, basic CrewAI concepts
**Related Docs:** [CLAUDE.md](../../CLAUDE.md), [COMMON_ERRORS.md](../troubleshooting/COMMON_ERRORS.md)

## What You'll Build

In this tutorial, you'll create a complete **Book Recommendation Crew** from scratch. This crew will:

- Take a genre as input (e.g., "science fiction", "mystery")
- Research top 5 books in that genre
- Generate a structured DOCX report with book summaries, ratings, and purchase links
- Follow all epic_news architectural patterns

By the end, you'll understand:
- The two-agent pattern (researcher + reporter)
- How to define agents and tasks in YAML
- How to create Pydantic models (Python 3.13 syntax)
- How to build a DOCX assembler
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
- `src/epic_news/utils/docx_report/crews/book_recommender.py` - DOCX assembler

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

## Step 4: Create Pydantic Model

Create `src/epic_news/models/crews/book_recommendation_report.py`:

```python
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
    summary: str | None = Field(None, description="Overall genre summary")


```

**Syntax note:** use Python 3.13 union syntax (`str | None`) for optional
fields. CrewAI 1.8.0+ handles it, and Ruff (UP007/UP045) rewrites legacy
`Optional[X]` / `Union[X, Y]` automatically.

## Step 5: Implement Crew Class

Create `book_recommender_crew.py`:

```python
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

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        """Research agent with search and scraping tools."""
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
            tools=get_search_tools() + get_scrape_tools(),  # Tools assigned in code, NOT YAML
            llm=LLMConfig.get_openrouter_llm(task_type="default"),  # timeout lives on the LLM
            max_iter=LLMConfig.get_max_iter(),  # Agent field
            respect_context_window=True,
        )

    @agent
    def reporter(self) -> Agent:
        """Reporting agent with NO tools for clean JSON output."""
        return Agent(
            config=self.agents_config["reporter"],
            verbose=True,
            tools=[],  # NO TOOLS: formatting only
            llm=LLMConfig.get_openrouter_llm(task_type="default"),
            max_iter=LLMConfig.get_max_iter(),
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
                max_rpm=LLMConfig.get_max_rpm(),  # Crew has no max_iter / llm_timeout fields
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
   Don't define tools in `agents.yaml`: CrewBase only resolves YAML tool names
   against `@tool` methods on the crew class, otherwise it raises `KeyError`.

2. **Two-Agent Pattern**:
   - `researcher`: Has tools, no `output_file`
   - `reporter`: NO tools, has `output_pydantic`
   - `output_pydantic` keeps action traces out of the result; the reporter stays tool-free so it only formats

3. **LLMConfig usage**:
   ```python
   llm=LLMConfig.get_openrouter_llm(task_type="default")  # ✅ timeout set on the LLM
   max_iter=LLMConfig.get_max_iter()  # ✅ on the Agent
   ```
   Never hardcode model names or timeouts, and never pass `llm_timeout=`:
   CrewAI silently ignores unknown keyword arguments.

4. **system_template**: Explicit JSON formatting instructions prevent escaping errors

## Step 6: Create the DOCX Assembler

Create `src/epic_news/utils/docx_report/crews/book_recommender.py`. An assembler turns the
validated model into Markdown fragments and calls `build_docx`, which runs pandoc and
refuses any path outside `output/`. This one is deterministic (no LLM call); see
`saint.py` in the same folder for an assembler that narrates sections with the LLM.

```python
"""Book recommendations -> DOCX: deterministic, no LLM."""

from typing import Any

from epic_news.models.crews.book_recommendation_report import BookDetail, BookRecommendationReport
from epic_news.utils.docx_report import build_docx


def _book_markdown(book: BookDetail) -> str:
    lines = [
        f"**{book.author}** ({book.publication_year}), rating {book.rating}/5",
        "",
        book.summary,
    ]
    if book.themes:
        lines += ["", "Themes: " + ", ".join(book.themes)]
    lines += [f"- [{link.retailer}]({link.url})" for link in book.purchase_links]
    return "\n".join(lines)


def assemble_book_recommender_docx(
    model: BookRecommendationReport, inputs: dict, output_path: str, llm: Any = None
) -> str:
    """Build the report as a DOCX. `llm` is unused (kept for the common assembler signature)."""
    fragments = [(book.title, _book_markdown(book)) for book in model.books]
    if model.summary:
        fragments.insert(0, ("Overview", model.summary))
    meta = {
        "title": f"Book recommendations: {model.genre}",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return build_docx(fragments, meta, output_path)
```

**Key points:**

1. **Handle empty states**: skip optional parts (`if model.summary:`) instead of writing empty headings.
2. **Keep paths under `output/`**: `build_docx` raises `ValueError` otherwise.
3. **Let errors propagate**: a report that cannot be built stops the run, and no email is sent.

## Step 7: Integrate with ReceptionFlow

Register the crew in `src/epic_news/crew_registry.py`: add a member to the `CrewKey` enum
and a `CrewSpec` keyed by it. The key is also the classifier category, so a crew missing
from the registry is never offered to the classifier:

```python
from epic_news.models.crews.book_recommendation_report import BookRecommendationReport
from epic_news.utils.docx_report.crews.book_recommender import assemble_book_recommender_docx

# in CrewKey:
    BOOK_RECOMMENDER = "BOOK_RECOMMENDER"

# in _SPECS:
    CrewSpec(
        CrewKey.BOOK_RECOMMENDER,
        "Recommandations de lecture",
        BookRecommendationReport,
        "output/book_recommender/report.json",
        "output/book_recommender/report.docx",
        assemble_book_recommender_docx,
    ),

# and add CrewKey.BOOK_RECOMMENDER to STANDARD_CREWS
```

Then edit `src/epic_news/main.py`: route the key in `determine_crew`, add a
`generate_*` step, and add the step name to `send_email`'s `or_(...)`:

```python
from epic_news.crews.book_recommender.book_recommender_crew import BookRecommenderCrew


class ReceptionFlow(Flow[ContentState]):
    # ... existing code ...

    # In determine_crew():
    #     if self.state.selected_crew == CrewKey.BOOK_RECOMMENDER:
    #         return "go_generate_book_recommendations"

    @listen("go_generate_book_recommendations")
    @trace_task(tracer)
    def generate_book_recommendations(self):
        """Generate book recommendations for a genre."""
        inputs = self.state.to_crew_inputs()
        self._run_standard(CREW_REGISTRY[CrewKey.BOOK_RECOMMENDER], BookRecommenderCrew(), inputs)
```

`_run_standard` deletes a JSON left by an earlier run, runs the crew, loads the model
from `json_path` (falling back to the raw crew output) and builds the DOCX with the
spec's assembler. Set `output_file: '{output_file}'` on the reporting task: the helper
passes `json_path` as that input. `tests/test_crew_registry.py` fails until the registry,
`determine_crew` and the `@listen` step agree.

## Step 8: Test Your Crew

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
3. DOCX report generated at `output/book_recommender/report.docx`
4. Open the DOCX file in Word (or LibreOffice) to see your formatted report

## Step 9: Write Structure Tests

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


def test_assembler_exists():
    """Test that the assembler exists and is importable."""
    from epic_news.utils.docx_report.crews.book_recommender import (
        assemble_book_recommender_docx,
    )

    assert callable(assemble_book_recommender_docx)


def test_crew_instantiation():
    """Test that crew can be instantiated."""
    from epic_news.crews.book_recommender.book_recommender_crew import (
        BookRecommenderCrew,
    )

    crew_instance = BookRecommenderCrew()
    assert crew_instance is not None
    assert crew_instance.crew() is not None


def test_assembler_output(tmp_path, monkeypatch):
    """Test that the assembler writes a DOCX under output/ (needs pandoc)."""
    from epic_news.models.crews.book_recommendation_report import BookRecommendationReport
    from epic_news.utils.docx_report.crews.book_recommender import (
        assemble_book_recommender_docx,
    )

    monkeypatch.chdir(tmp_path)  # build_docx only writes inside ./output
    report = BookRecommendationReport(
        genre="science fiction",
        generation_date="2024-01-15",
        books=[
            {
                "title": "Test Book",
                "author": "Test Author",
                "publication_year": 2020,
                "rating": 4.5,
                "summary": "A test book summary.",
                "themes": ["space", "adventure"],
                "purchase_links": [{"retailer": "Amazon", "url": "https://amazon.com"}],
            }
        ],
    )

    path = assemble_book_recommender_docx(report, {}, "output/book_recommender/report.docx")

    assert path.endswith(".docx")
    assert (tmp_path / path).stat().st_size > 0


def test_assembler_refuses_paths_outside_output(tmp_path, monkeypatch):
    """Test that build_docx refuses a path outside output/."""
    from epic_news.utils.docx_report import build_docx

    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        build_docx([("Title", "text")], {"title": "T"}, str(tmp_path / "elsewhere.docx"))
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

### Issue 2: Action Traces in the Report

**Error:** The report or JSON file contains agent thinking/tool calls instead of clean content.

**Solution:** Use `output_pydantic` on the final task and the **two-agent pattern** - the reporter agent has no tools and owns the `output_file`. See [Crew Execution Errors](../troubleshooting/COMMON_ERRORS.md#crew-execution-errors).

### Issue 3: AttributeError with Union Types

**Error:**
```
AttributeError: 'UnionType' object has no attribute 'copy_with'
```

**Solution:** This only happened with CrewAI < 1.8.0. Upgrade CrewAI; `X | None` is the project standard.

### Issue 4: KeyError for Tools

**Error:**
```
KeyError: '<ToolName>'
```

**Solution:** Don't define tools in YAML (names only resolve against `@tool` methods) - assign them programmatically in the `@agent` method. See [Crew Execution Errors](../troubleshooting/COMMON_ERRORS.md#crew-execution-errors).

### Issue 5: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'epic_news'
```

**Solution:** Run `uv pip install -e .` for editable install. See [Import/Module Errors](../troubleshooting/COMMON_ERRORS.md#importmodule-errors).

### Issue 6: `Refusing to write a report outside output/`

**Symptom:** `build_docx` raises `ValueError`.

**Solution:** Build the output path under `output/` (for example `output/book_recommender/report.docx`). See [DOCX Report Issues](../troubleshooting/COMMON_ERRORS.md#docx-report-issues).

## Key Takeaways

✅ **Always use the two-agent pattern** for reports (researcher + reporter)
✅ **Assign tools in Python code**, never in YAML
✅ **Use Python 3.13 union syntax** (`X | None`)
✅ **Add system_template** to reporter agents for JSON formatting
✅ **Keep report paths under `output/`**; a build error stops the run
✅ **Handle empty states** gracefully in assemblers
✅ **Use `LLMConfig`** methods (`get_openrouter_llm(task_type=...)`, `max_iter` on Agent), never hardcode LLM settings
✅ **Write structure tests** to ensure crew integrity

## Next Steps

- **Tutorial 2:** Adding Custom Tools (Coming soon)
- **Reference:** [DOCX-only reports (ADR-017)](../adr/ADR-017-docx-only-reports.md)
- **Reference:** [Tools Reference](../reference/tools.md)
- **How-to:** [Troubleshooting](../how-to/troubleshooting.md)

## Need Help?

- Check [COMMON_ERRORS.md](../troubleshooting/COMMON_ERRORS.md) for troubleshooting
- Review [CLAUDE.md](../../CLAUDE.md) for architectural patterns
- Examine existing crews in `src/epic_news/crews/` for examples
- Ask questions in the project repository

---

**Congratulations!** You've successfully created your first epic_news crew. You now understand the complete workflow from YAML configuration to the DOCX report.
