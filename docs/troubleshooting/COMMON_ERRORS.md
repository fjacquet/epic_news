# Epic News Troubleshooting Guide

**Last Updated:** 2026-01-10
**Target Audience:** All developers working with epic_news

## Quick Navigation

- [JSON Escaping Errors](#json-escaping-errors) ← **START HERE** if you see "invalid escape" or "invalid character"
- [Pydantic Validation Errors](#pydantic-validation-errors)
- [Crew Execution Errors](#crew-execution-errors)
- [HTML Rendering Issues](#html-rendering-issues)
- [Tool/API Errors](#toolapi-errors)
- [Import/Module Errors](#importmodule-errors)
- [Performance Issues](#performance-issues)

---

## JSON Escaping Errors

### Error: Invalid JSON escape at line X column Y

**Real-World Example (Poem Crew):**
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for PoemJSONOutput
  Invalid JSON: invalid escape at line 3 column 753 [type=json_invalid, input_value='{\n  "title": "Chant du ...humilité dédiée."\n}', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/json_invalid
```

#### Root Cause

The LLM generated JSON containing unescaped special characters, particularly:
- **French apostrophes**: "l'humilité" should be "l\\'humilité"
- **Quotes inside strings**: Not escaped with `\"`
- **Other special characters**: Backslashes, newlines not properly escaped

This happens most commonly with:
1. Non-English text (French, Spanish, German with special characters)
2. Poetry or creative writing (contains quotes, apostrophes)
3. User-generated content (unpredictable characters)
4. Complex descriptions with nested quotes

#### Symptoms

- Error message contains "invalid escape" or "invalid character"
- Error occurs during Pydantic validation (`model_validate_json`)
- Input value preview shows normal-looking JSON in error message
- Happens inconsistently (depends on LLM output content)

#### Solution 1: Add system_template to Agent (RECOMMENDED)

Add explicit JSON formatting instructions to the agent that generates JSON output:

```python
@agent
def poem_writer(self) -> Agent:
    return Agent(
        config=self.agents_config["poem_writer"],
        llm=LLMConfig.get_openrouter_llm(),
        llm_timeout=LLMConfig.get_timeout("default"),
        respect_context_window=True,
        verbose=True,
        system_template="""You are a JSON formatting expert. Your output MUST be valid JSON.

        CRITICAL JSON FORMATTING RULES:
        - ALL string values must have special characters properly escaped
        - Use \\" for quotes inside strings
        - Use \\\\ for backslashes
        - French apostrophes MUST be escaped: "l'amour" → "l\\'amour"
        - Common patterns to escape:
          * "C'est" → "C\\'est"
          * "d'une" → "d\\'une"
          * "l'humilité" → "l\\'humilité"
          * Any ' inside strings → \\'

        Output ONLY valid JSON with properly escaped strings. No markdown, no explanations.""",
    )
```

**Why this works:**
- Gives the LLM explicit JSON escaping rules
- Focuses attention on special character handling
- Works preventatively before JSON is generated

**File changed:**
- `/src/epic_news/crews/poem/poem_crew.py` (lines 13-35)

---

#### Solution 2: Add Pydantic Field Validators

Add validators to automatically clean text fields:

```python
# src/epic_news/models/crews/poem_report.py
from pydantic import BaseModel, Field, field_validator

class PoemJSONOutput(BaseModel):
    """Schema ensuring tasks return a single valid JSON object for a poem."""

    title: str = Field(..., description="The title of the poem.")
    poem: str = Field(..., description="The full text of the poem.")

    @field_validator('title', 'poem', mode='before')
    @classmethod
    def clean_text(cls, v):
        """Clean and normalize text with special characters."""
        if isinstance(v, str):
            # Fix common escape issues
            v = v.replace("'", "\\'")  # Escape single quotes
            v = v.replace('"', '\\"')  # Escape double quotes
            # Note: Only do this if JSON parsing fails
        return v
```

**Caution:** This approach can cause double-escaping if the JSON is already properly formatted. Use only if `system_template` doesn't work.

---

#### Solution 3: Pre-process JSON String

Add a JSON cleaning utility:

```python
# src/epic_news/utils/json_validation.py
import json
import re
from typing import Any

def clean_llm_json(raw_json: str) -> str:
    """Clean and validate JSON from LLM output.

    Handles:
    - Markdown code blocks
    - Common escape issues
    - Malformed JSON strings
    """
    # Remove markdown code blocks
    raw_json = re.sub(r'```json\n?|```', '', raw_json.strip())

    try:
        # Try to parse - this will fail if there are escape issues
        data = json.loads(raw_json)
        # Re-serialize to ensure proper escaping
        return json.dumps(data, ensure_ascii=False)
    except json.JSONDecodeError as e:
        # Attempt to fix common escape issues
        # Replace unescaped apostrophes in likely positions
        fixed_json = re.sub(r"([^\\])'", r"\1\\'", raw_json)

        try:
            data = json.loads(fixed_json)
            return json.dumps(data, ensure_ascii=False)
        except json.JSONDecodeError:
            # Last resort: return original and let Pydantic fail with clear error
            return raw_json
```

**Usage in crew execution:**
```python
result = PoemCrew().crew().kickoff(inputs=inputs)
cleaned_json = clean_llm_json(result.raw)
report = PoemJSONOutput.model_validate_json(cleaned_json)
```

---

#### Prevention Checklist

- [ ] Agent generating JSON has `system_template` with escaping rules
- [ ] Test with non-English text during development (French, Spanish, German)
- [ ] Test with special characters (quotes, apostrophes, backslashes)
- [ ] Add Pydantic validators for text-heavy fields (poems, descriptions)
- [ ] Use JSON cleaning utility for user-generated content
- [ ] Log raw JSON output for debugging (`print(result.raw)`)

---

#### Testing the Fix

```bash
# Test with French input
crewai flow kickoff

# When prompted:
> "Get me a poem about l'amour and l'humilité"

# Check for successful execution (no ValidationError)
```

**Expected result:** Poem generated successfully without validation errors.

---

## Pydantic Validation Errors

### Error: AttributeError: 'UnionType' object has no attribute '__name__'

#### Symptom

```
AttributeError: 'UnionType' object has no attribute '__name__'
  at PydanticSchemaParser.get_schema()
```

#### Root Cause

Python 3.10+ Union syntax (`X | Y`) is incompatible with CrewAI's schema parser. CrewAI requires legacy `typing.Union` syntax.

#### Solution

```python
from typing import Union, Optional, List  # Import legacy types

# ❌ WRONG - Modern Python 3.10+ syntax
class Report(BaseModel):
    title: str | None = None
    count: int | float = 0
    items: list[str] = []

# ✅ CORRECT - Legacy syntax for CrewAI
class Report(BaseModel):
    title: Optional[str] = None
    count: Union[int, float] = 0
    items: List[str] = []
```

#### Find/Replace for Fixing

**Pattern 1: Optional fields**
- Find: `: (\w+) \| None`
- Replace: `: Optional[$1]`

**Pattern 2: Union types**
- Find: `: (\w+) \| (\w+)`
- Replace: `: Union[$1, $2]`

**Pattern 3: Generic types**
- Find: `: list\[(\w+)\]`
- Replace: `: List[$1]`

#### Reference

See **CLAUDE.md** section: "Pydantic Models: Legacy Union Syntax Required"

---

### Error: ValidationError - field required

#### Symptom

```
pydantic.ValidationError: 1 validation error
field_name
  field required (type=value_error.missing)
```

#### Root Cause

The LLM output doesn't include a required field, or the field name doesn't match the Pydantic model.

#### Debugging Steps

1. **Dump raw output:**
```python
result = MyCrew().crew().kickoff(inputs=inputs)
print("=== RAW OUTPUT ===")
print(result.raw)
print("=== END RAW OUTPUT ===")
```

2. **Check field name mapping:**
```python
import json
raw_data = json.loads(result.raw)
print(f"LLM returned fields: {list(raw_data.keys())}")
print(f"Model expects fields: {MyModel.model_fields.keys()}")
```

3. **Make fields optional temporarily:**
```python
class Report(BaseModel):
    required_field: str
    optional_field: Optional[str] = "default"  # Won't fail if missing
```

#### Solutions

**Option 1: Fix field names in model**
```python
class Report(BaseModel):
    # Match what LLM actually returns
    summary: str = Field(..., alias="description")  # LLM returns "description"
```

**Option 2: Normalize data before validation**
```python
raw_data = json.loads(result.raw)
if "description" in raw_data and "summary" not in raw_data:
    raw_data["summary"] = raw_data["description"]  # Normalize field name

report = Report(**raw_data)
```

**Option 3: Update task description**
```yaml
# tasks.yaml - Be explicit about field names
research_task:
  expected_output: |
    JSON with EXACTLY these fields:
    - summary (string, required)
    - date (string, ISO format, required)
    - author (string, required)
```

---

## Crew Execution Errors

### Error: HTML output contains action traces, not final report

#### Symptom

HTML file contains:
```html
<html>
Action: Search the web
Action Input: {"query": "..."}
Observation: ...
Final Answer: <actual content>
</html>
```

#### Root Cause

Reporter agent has tools assigned, which causes CrewAI to write action logs to the output file.

#### Solution

Follow the **two-agent pattern**:
1. **Research agent**: Has tools, no `output_file`
2. **Reporter agent**: NO tools, has `output_file` or `output_pydantic`

```python
# ❌ WRONG
@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[SearchTool()],  # Tools cause action traces in output
        output_file="report.html",
    )

# ✅ CORRECT
@agent
def researcher(self) -> Agent:
    return Agent(
        tools=get_search_tools(),  # Has tools
        # No output_file
    )

@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[],  # NO TOOLS = Clean output
    )

@task
def reporting_task(self) -> Task:
    return Task(
        agent=self.reporter(),
        context=[self.research_task()],  # Gets data from researcher
        output_pydantic=MyReport,
    )
```

#### Reference

See **CLAUDE.md** section: "HTML Report Generation: Two-Agent Pattern"

---

### Error: KeyError when crew initializes

#### Symptom

```
KeyError: 'tool_name'
```

#### Root Cause

Tools defined in `agents.yaml` instead of Python code. CrewAI requires tools to be assigned programmatically.

#### Solution

```yaml
# ❌ WRONG - agents.yaml
researcher:
  role: "Researcher"
  tools:
    - SearchTool  # Don't define tools in YAML
```

```python
# ✅ CORRECT - crew.py
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["researcher"],
        tools=get_search_tools(),  # Assign tools in code
    )
```

#### Reference

See **CLAUDE.md** section: "CRITICAL: Tools must be assigned programmatically in the `@agent` method"

---

### Error: Crew runs but produces empty/incomplete output

#### Symptoms

- HTML file exists but has minimal/no content
- Report is generated but missing sections
- Execution completes without errors but output is incomplete

#### Debugging Checklist

**1. Check LLM timeout:**
```python
@crew
def crew(self) -> Crew:
    return Crew(
        llm_timeout=LLMConfig.get_timeout("long"),  # Increase from "default" (300s) to "long" (600s)
    )
```

**2. Enable verbose logging:**
```python
@agent
def researcher(self) -> Agent:
    return Agent(
        verbose=True,  # See agent reasoning process
    )
```

**3. Check crew logs:**
```bash
tail -f logs/epic_news.log
# Look for: timeouts, errors, incomplete responses
```

**4. Validate task expected_output:**
```yaml
# tasks.yaml - Be specific about requirements
research_task:
  expected_output: |
    JSON with fields: title, summary, date, author
    Minimum 5 items required
    Each item must have all fields populated
```

**5. Check max_iter limit:**
```python
@crew
def crew(self) -> Crew:
    return Crew(
        max_iter=5,  # If agent is looping, increase this
    )
```

---

## HTML Rendering Issues

### Error: CSS classes not applied (shows `class_="..."` in HTML)

#### Symptom

Generated HTML contains:
```html
<div class_="container">  <!-- Invalid attribute -->
```

#### Root Cause

BeautifulSoup's `class_` parameter has escaping issues. Must use `attrs` dictionary instead.

#### Solution

```python
# ❌ WRONG
tag = soup.new_tag("div", class_="container")

# ✅ CORRECT
tag = soup.new_tag("div")
tag.attrs["class"] = ["container", "my-class"]  # Multiple classes as list
```

#### Reference

See **3_ARCHITECTURAL_PATTERNS.md** section: "BeautifulSoup Class Attribute Handling"

---

### Error: Renderer not found for crew identifier

#### Symptom

```
ValueError: No renderer found for crew identifier 'my_crew'
```

#### Solution Checklist

**1. Create renderer class:**
```python
# src/epic_news/utils/html/template_renderers/my_crew_renderer.py
from epic_news.utils.html.template_renderers.base_renderer import BaseRenderer

class MyCrewRenderer(BaseRenderer):
    crew_identifier = "my_crew"  # MUST match factory usage

    def __init__(self):  # REQUIRED even if empty
        super().__init__()

    def render_body(self, soup, data):
        container = soup.new_tag("div")
        container.attrs["class"] = ["container", "py-4"]
        # ... build HTML
        return container
```

**2. Verify file naming:**
- File: `my_crew_renderer.py`
- Class: `MyCrewRenderer`
- Identifier: `"my_crew"`

**3. Check TemplateManager registration:**
```bash
python -c "from epic_news.utils.html.template_manager import TemplateManager; print(list(TemplateManager._renderers.keys()))"
# Should include 'my_crew'
```

---

## Tool/API Errors

### Error: 401 Unauthorized or 403 Forbidden

#### Symptom

```
HTTPStatusError: 401 Unauthorized
```

#### Solution Checklist

**1. Check .env file:**
```bash
cat .env | grep API_KEY
# Verify key exists and is not empty
```

**2. Restart if .env changed:**
```bash
# .env changes require restart
crewai flow kickoff
```

**3. Validate key in provider dashboard:**
- Log into provider (OpenRouter, Serper, Tavily, etc.)
- Verify key is active and has credits/quota remaining
- Check if key has correct permissions

**4. Check API endpoint:**
```python
# Verify correct base URL
llm = LLM(
    model="openrouter/...",
    base_url="https://openrouter.ai/api/v1",  # Correct endpoint
)
```

---

### Error: 429 Too Many Requests (Rate Limit)

#### Symptom

```
HTTPStatusError: 429 Too Many Requests
```

#### Solution

**1. Reduce max_rpm:**
```python
@crew
def crew(self) -> Crew:
    return Crew(
        max_rpm=10,  # Reduce from default 20
    )
```

**2. Enable tool caching:**
```python
from crewai_tools import TavilyTool

tool = TavilyTool(cache=True)  # Reuse results within session
```

**3. Add retry logic:**
```python
@crew
def crew(self) -> Crew:
    return Crew(
        max_retry_limit=3,  # Retry failed API calls
    )
```

**4. Batch operations:**
- Process multiple items in one crew run
- Avoid separate crew executions per item

---

## Import/Module Errors

### Error: ModuleNotFoundError: No module named 'epic_news'

#### Symptom

```
ModuleNotFoundError: No module named 'epic_news'
```

#### Root Cause

Package not installed in editable mode. Python can't find the `epic_news` module.

#### Solution

```bash
uv pip install -e .
```

**Why editable mode?**
- Creates symlink so Python finds `epic_news` package
- Changes to code are immediately available
- No need to reinstall after each edit

**Verify installation:**
```bash
uv pip list | grep epic-news
# Should show: epic-news (editable install)
```

---

### Error: Circular import

#### Symptom

```
ImportError: cannot import name 'X' from partially initialized module 'Y'
```

#### Solution

**Option 1: Move import to function scope**
```python
# ❌ WRONG - Top level import
from epic_news.utils.helper import func

def my_function():
    return func()

# ✅ CORRECT - Inside function
def my_function():
    from epic_news.utils.helper import func
    return func()
```

**Option 2: Restructure dependencies**
- Extract shared code to separate module
- Use dependency injection instead of direct imports
- Avoid importing from `__init__.py` files

---

## Performance Issues

### Issue: Crew takes > 5 minutes to complete

#### Diagnosis Steps

**1. Check LLM timeout:**
```python
# Is it timing out?
@crew
def crew(self) -> Crew:
    return Crew(
        llm_timeout=LLMConfig.get_timeout("long"),  # 600s
    )
```

**2. Profile tool calls:**
```bash
# Count API calls in logs
grep "Action:" logs/epic_news.log | wc -l
```

**3. Check for agent loops:**
```bash
# Look for repeated actions
grep "Action:" logs/epic_news.log | tail -20
```

**4. Monitor max_iter:**
```python
@crew
def crew(self) -> Crew:
    return Crew(
        max_iter=3,  # Reduce from 5 if agent loops
    )
```

#### Optimization Strategies

**1. Use faster models for simple tasks:**
```python
# Quick tasks (classification, simple extraction)
llm=LLMConfig.get_openrouter_llm()  # Uses MODEL from .env

# Switch model via .env:
# MODEL=openrouter/google/gemini-flash-1.5  # Fast, cheap
```

**2. Enable tool caching:**
```python
from crewai_tools import TavilyTool

tool = TavilyTool(cache=True)  # Reuse results
```

**3. Parallelize independent tasks:**
```python
@task
def task1(self) -> Task:
    return Task(
        async_execution=True,  # Run in parallel
    )

@task
def task2(self) -> Task:
    return Task(
        async_execution=True,  # Run in parallel
    )
```

**4. Reduce max_rpm for stability:**
```python
@crew
def crew(self) -> Crew:
    return Crew(
        max_rpm=10,  # Fewer concurrent requests
    )
```

---

## Debugging Checklist

When you encounter any error:

- [ ] Read the **full stack trace** (don't just look at last line)
- [ ] Check logs: `tail -f logs/epic_news.log`
- [ ] Verify .env file has required API keys
- [ ] Confirm package installed: `uv pip install -e .`
- [ ] Check Pydantic models use legacy Union syntax (`Optional[X]` not `X | None`)
- [ ] Validate crew structure: researcher (tools) + reporter (no tools)
- [ ] Enable verbose mode: `verbose=True` on agents
- [ ] Dump raw output: `print(result.raw)`
- [ ] Test crew in isolation (not through ReceptionFlow)
- [ ] Search this guide for error message keywords

---

## Still Stuck?

### 1. Search existing documentation

- **CLAUDE.md** for architectural patterns and critical rules
- **1_DEVELOPMENT_GUIDE.md** for setup and workflow issues
- **3_ARCHITECTURAL_PATTERNS.md** for design solutions
- **2_TOOLS_HANDBOOK.md** for tool usage patterns

### 2. Check example crews

Study working crews for patterns:
- **poem** - Simple single-agent crew
- **cooking** - Medium complexity
- **library** - Two-agent pattern with HTML output
- **fin_daily** - Complex with async execution

### 3. Enable debug logging

```python
from loguru import logger

# In your code
logger.add("debug.log", level="DEBUG")
logger.debug(f"State: {self.state}")
logger.debug(f"Inputs: {crew_inputs}")
logger.debug(f"Raw output: {result.raw}")
```

### 4. Create minimal reproduction

Isolate the problem:
```python
# test_minimal.py
from epic_news.crews.my_crew.my_crew import MyCrew

inputs = {"topic": "test"}
result = MyCrew().crew().kickoff(inputs=inputs)
print(result.raw)
```

### 5. Ask for help with context

Include:
- Error message with full stack trace
- Relevant code (crew definition, model, renderer)
- What you tried
- What you expected vs. what happened

---

## Summary

**Most Common Errors:**

1. **JSON escaping** - Use `system_template` with explicit escaping rules
2. **Pydantic Union syntax** - Use `Optional[X]` not `X | None`
3. **Action traces in HTML** - Two-agent pattern (researcher + reporter)
4. **Tools in YAML** - Assign tools in Python code, not YAML
5. **ModuleNotFoundError** - Run `uv pip install -e .`

**Quick Fixes:**

| Error | Quick Fix |
|-------|-----------|
| JSON escaping | Add `system_template` to agent |
| Union syntax | Replace `X \| None` with `Optional[X]` |
| Action traces | Reporter agent must have `tools=[]` |
| Tools KeyError | Move tool assignment from YAML to Python |
| Module not found | Run `uv pip install -e .` |
| 401 Unauthorized | Check API keys in `.env` |
| 429 Rate limit | Reduce `max_rpm` in crew config |

**Next Steps:**

- [Development Guide](../docs/1_DEVELOPMENT_GUIDE.md) - Setup and workflow
- [Architectural Patterns](../docs/3_ARCHITECTURAL_PATTERNS.md) - Design patterns
- [Your First Crew Tutorial](../tutorials/01_YOUR_FIRST_CREW.md) - Step-by-step guide (coming soon)

---

**Last Updated:** 2026-01-10
