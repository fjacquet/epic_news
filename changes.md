### 1. Eliminate `utils/html` in Favor of Deterministic Rendering

- [ ] **Issue:** The `utils/html` directory contains numerous `*_html_factory.py` files that manually construct HTML. This is brittle and inconsistent with the "Deterministic Python-Based Rendering" pattern described in the architecture guide, which favors `TemplateManager`.
- [ ] **Recommendation:**
  - [ ] **Delete `utils/html`:** Remove the entire `src/epic_news/utils/html` directory.
  - [ ] **Refactor to Use `TemplateManager`:** Modify all crew handlers in `main.py` to pass the Pydantic model output directly to `TemplateManager` for rendering, as demonstrated by the `saint_to_html` example in the documentation. This ensures all HTML generation is centralized and consistent.
- [ ] **Files:**
  - `src/epic_news/utils/html/` (delete entire directory)
  - `src/epic_news/main.py` (update all `generate_*` methods)

### 2. Remove Redundant `bin` Scripts

- [ ] **Issue:** The `src/epic_news/bin` directory contains several debug and analysis scripts (`analyze_library_crew.py`, `debug_holiday_plan_html.py`, etc.). These are useful for development but add clutter to the `src` directory.
- [ ] **Recommendation:**
  - [ ] **Move Scripts to a `scripts` Directory:** Relocate these helper scripts to a top-level `scripts/` directory to separate them from the core application source code.
  - [ ] **Improve Script Quality:** Ensure scripts follow the same coding standards as the main application (e.g., use `loguru`, `pathlib`).
- [ ] **Files:** `src/epic_news/bin/`

### 3. Standardize Logging

- [ ] **Issue:** The `app.py` (Streamlit UI) uses the standard `logging` module, while the rest of the application is meant to use `loguru` as per the development guide.
- [ ] **Recommendation:**
  - [ ] **Replace `logging` with `loguru` in `app.py`:** Refactor `app.py` to use `loguru` for all logging, consistent with the rest of the project. The `QueueLogger` can be adapted for `loguru`.
- [ ] **File:** `src/epic_news/app.py`

### 4. Remove Unused and Deprecated Code

- [ ] **Issue:** There are several commented-out code blocks and unused imports across various files (e.g., `company_news_crew.py` has a commented-out `fact_checker` agent).
- [ ] **Recommendation:**
  - [ ] **Perform a Code Cleanup:** Systematically review all files in `src/` and remove dead code, commented-out blocks, and unused imports. This improves readability and reduces maintenance overhead.
- [ ] **Files:**
  - `src/epic_news/crews/company_news/company_news_crew.py`
  - ... and others.

### 5. Refactor `ContentState` Model

- [ ] **Issue:** The `ContentState` model in `src/epic_news/models/content_state.py` has a large number of `Union[Any, None]` fields for crew results. This is not type-safe and makes it hard to understand the expected data structure for each crew.
- [ ] **Recommendation:**
  - [ ] **Use Specific Pydantic Models:** For each crew result field (e.g., `company_profile`, `tech_stack`), use the specific Pydantic model that the crew is expected to return (e.g., `CompanyProfile`, `TechStackReport`). This will improve type safety and clarity.
- [ ] **File:** `src/epic_news/models/content_state.py`

### 6. Standardize Pydantic Optional Fields

- [ ] **Issue:** The use of `Union[X, None]` and `Optional[X]` for optional fields is inconsistent across the Pydantic models.
- [ ] **Recommendation:**
  - [ ] **Standardize on `Optional[X]`:** Refactor all optional fields in Pydantic models to use `from typing import Optional` and `Optional[X]`. This is functionally identical to `Union[X, None]` but is more explicit and idiomatic for declaring optional fields.
  - [ ] **Strictly Avoid `|`:** This refactoring will be done while strictly adhering to the project rule of **never** using the `|` operator for unions (e.g., `str | None`), which is incompatible with CrewAI.
- [ ] **Files:** `src/epic_news/models/`
