# To-Do

## 🔥 Next Up (Priority)

- [x] **Create HTML Report for Cross-Reference Crew**
  - [x] **Create HTML Factory**: `src/epic_news/utils/html/cross_reference_report_html_factory.py`
  - [x] **Create HTML Template**: `templates/cross_reference_report_template.html`
  - [x] **Fix Regeneration Script**: `tests/bin/regenerate_cross_reference_report.py` to dynamically handle the target.
  - [x] **Verify**: Run the regeneration script and the full test suite.
- [x] **Integrate HTML generation into `main.py`**

---
*Original To-Do Items Continue Below*
---

### 2. Full Pydantic Model & Directory Refactoring

*This is a comprehensive refactoring to improve modularity, reliability, and data quality across the application. It involves relocating all crew-specific Pydantic models to a dedicated directory and then refactoring five key OSINT crews to use structured outputs.*

-   [x] **Phase 1: Create New Model Structure**
    -   [x] Create the new directory: `src/epic_news/models/crews/`.
    -   [x] **Move existing crew-specific models** to the new directory and rename where necessary.
    -   [x] **Create the 5 new OSINT report model files** in the new directory.

-   [x] **Phase 2: Create Model Tests**
    -   [x] Create and validate tests for all new and relocated models.

-   [x] **Phase 3: Update All Project Import Paths & Fix Tests**
    -   [x] Update all import statements in the project to point to the new model locations.
    -   [x] Run the full test suite and fix all resulting errors.

-   [x] **Phase 4: Refactor `CompanyProfilerCrew` (Corrected)**
    -   [x] **YAML**: Ensure `company_reporter` agent in `agents.yaml` has `tools: []`.
    -   [x] **Python**: In `company_profiler_crew.py`, import `CompanyProfileReport` and add `output_pydantic=CompanyProfileReport` to the final `Task`.
    -   [x] **Verify**: Run the crew and `uv run pytest`.

-   [x] **Phase 5: Refactor `CrossReferenceReportCrew` (Corrected)**
    -   [x] **YAML**: Ensure `osint_reporter` agent in `agents.yaml` has `tools: []`.
    -   [x] **Python**: In `cross_reference_report_crew.py`, import `CrossReferenceReport` and add `output_pydantic=CrossReferenceReport` to the final `Task`.
    -   [x] **Verify**: Run the crew and `uv run pytest`.

-   [x] **Phase 6: Refactor `GeospatialAnalysisCrew` (Corrected)**
    -   [x] **YAML**: Ensure `geospatial_reporter` agent in `agents.yaml` has `tools: []`.
    -   [x] **Python**: In `geospatial_analysis_crew.py`, import `GeospatialAnalysisReport` and add `output_pydantic=GeospatialAnalysisReport` to the final `Task`.
    -   [x] **Verify**: Run the crew and `uv run pytest`.

-   [x] **Phase 7: Refactor `HRIntelligenceCrew` (Corrected)**
    -   [x] **YAML**: Ensure `hr_reporter` agent in `agents.yaml` has `tools: []`.
    -   [x] **Python**: In `hr_intelligence_crew.py`, import `HRIntelligenceReport` and add `output_pydantic=HRIntelligenceReport` to the final `Task`.
    -   [x] **Verify**: Run the crew and `uv run pytest`.

-   [x] **Phase 8: Refactor `LegalAnalysisCrew` (Corrected)**
    -   [x] **YAML**: Ensure `legal_reporter` agent in `agents.yaml` has `tools: []`.
    -   [x] **Python**: In `legal_analysis_crew.py`, import `LegalAnalysisReport` and add `output_pydantic=LegalAnalysisReport` to the final `Task`.
    -   [x] **Verify**: Run the crew and `uv run pytest`.

-   [x] **Phase 9: Refactor `WebPresenceCrew` and `TechStackCrew` (Corrected)**
    -   [x] **YAML**: Ensure reporter agents in `agents.yaml` for both crews have `tools: []`.
    -   [x] **Python**: In `web_presence_crew.py` and `tech_stack_crew.py`, import the corresponding Pydantic models and add the `output_pydantic` parameter to the final `Task`.
    -   [x] **Verify**: Run the full test suite.

-   [x] **Phase 10: Final Verification**
    -   [x] **Final Regression Test**: After all refactoring is complete, run the full test suite one last time: `uv run pytest`.

* [x] **Refactor Logging to use Loguru**
  * [x] Add `loguru` to `pyproject.toml`.
  * [x] Replace the standard `logging` module with `loguru` across the application.
  * [x] Configure `loguru` sinks for console and file logging.
  * [x] Update the development guide with the new logging standards.

### 2. Remove Redundant `bin` Scripts

* [ ] **Issue:** The `src/epic_news/bin` directory contains several debug and analysis scripts (`analyze_library_crew.py`, `debug_holiday_plan_html.py`, etc.). These are useful for development but add clutter to the `src` directory.
* [ ] **Recommendation:**
  * [ ] **Move Scripts to a `scripts` Directory:** Relocate these helper scripts to a top-level `scripts/` directory to separate them from the core application source code.
  * [ ] **Improve Script Quality:** Ensure scripts follow the same coding standards as the main application (e.g., use `loguru`, `pathlib`).
* [ ] **Files:** `src/epic_news/bin/`

### 3. Standardize Logging

* [ ] **Issue:** The `app.py` (Streamlit UI) uses the standard `logging` module, while the rest of the application is meant to use `loguru` as per the development guide.
* [ ] **Recommendation:**
  * [ ] **Replace `logging` with `loguru` in `app.py`:** Refactor `app.py` to use `loguru` for all logging, consistent with the rest of the project. The `QueueLogger` can be adapted for `loguru`.
* [ ] **File:** `src/epic_news/app.py`

### 5. Refactor `ContentState` Model

* [ ] **Issue:** The `ContentState` model in `src/epic_news/models/content_state.py` has a large number of `Union[Any, None]` fields for crew results. This is not type-safe and makes it hard to understand the expected data structure for each crew.
* [ ] **Recommendation:**
  * [ ] **Use Specific Pydantic Models:** For each crew result field (e.g., `company_profile`, `tech_stack`), use the specific Pydantic model that the crew is expected to return (e.g., `CompanyProfile`, `TechStackReport`). This will improve type safety and clarity.
* [ ] **File:** `src/epic_news/models/content_state.py`

### 6. Standardize Pydantic Optional Fields

* [ ] **Issue:** The use of `Union[X, None]` and `Optional[X]` for optional fields is inconsistent across the Pydantic models.
* [ ] **Recommendation:**
  * [ ] **Standardize on `Optional[X]`:** Refactor all optional fields in Pydantic models to use `from typing import Optional` and `Optional[X]`. This is functionally identical to `Union[X, None]` but is more explicit and idiomatic for declaring optional fields.
  * [ ] **Strictly Avoid `|`:** This refactoring will be done while strictly adhering to the project rule of **never** using the `|` operator for unions (e.g., `str | None`), which is incompatible with CrewAI.
* [ ] **Files:** `src/epic_news/models/`

* [ ] **Réinjecter le rendu HTML dans les équipes**
  * [x] classify
  * [x] company_news
  * [x] cooking
  * [x] fin_daily
  * [x] holiday_planner
  * [x] html_designer
  * [x] library
  * [x] meeting_prep
  * [x] news_daily
  * [x] poem
  * [x] post
  * [x] reception
  * [x] rss_weekly
  * [x] saint_daily
  * [x] shopping_advisor
  * [ ] company_profiler
  * [ ] cross_reference_report_crew
  * [ ] geospatial_analysis
  * [ ] hr_intelligence
  * [x] information_extraction
  * [ ] legal_analysis
  * [ ] marketing_writers
  * [ ] menu_designer
  * [ ] sales_prospecting
  * [ ] tech_stack
  * [ ] web_presence

* [x] **Integrate Advanced Testing Libraries**
  * [x] Add `Faker` to `pyproject.toml` for generating realistic test data.
  * [x] Add `pytest-mock` to `pyproject.toml` for easier mocking in tests.
  * [x] Add `pendulum` to `pyproject.toml` for better date/time handling and time-freezing in tests.
  * [x] Run `uv sync` to install the new dependencies.
  * [x] Create a sample test in `tests/` demonstrating the usage of all three libraries.
  * [x] Update the `1_DEVELOPMENT_GUIDE.md` to include a section on these new testing standards.

* [ ] **Set up and execute CrewAI within a container environment.**
  * [x] Install Docker on the host machine.
  * [x] Pull the official CrewAI container image from the Docker registry.
  * [x] Create a Dockerfile to customize the CrewAI environment if needed.
  * [x] Build the Docker image using the Dockerfile.
  * [x] Run the CrewAI container with the necessary configurations and environment variables.
  * [ ] Verify the CrewAI execution and troubleshoot any issues that arise.

---

## 📋 Backlog (Future Tasks)

* [ ] **Connect n8n to retrieve data initiated by CrewAI.**
* [ ] **Connect n8n to initiate CrewAI integration.**
* [ ] **Créer des agents pour le suivi technologique**
  * [ ] Implement Nutanix AOS
  * [ ] Beta Netbackup
  * [ ] Implement Commvault B&R
  * [ ] PowerScale (Dell)
  * [ ] Eyeglass (Superna)
  * [ ] Suivi Tomcat
  * [ ] Implement Brocade FOS
  * [ ] Consul (HashiCorp)
  * [ ] Implement Cisco UCS
  * [ ] Implement Pure FlashArray
  * [ ] Packer (HashiCorp)
  * [ ] Suivi Nomad
  * [ ] Terraform (HashiCorp)
* [ ] **Add Free APIs to the project**
  * [ ] Research and identify potential free APIs that align with the project's goals.
  * [ ] Evaluate the documentation and usage limits of the selected APIs.
  * [ ] Create a plan for integrating the chosen APIs into the project.
  * [ ] Write the necessary code to connect to and fetch data from the APIs.
  * [ ] Test the API integrations to ensure they function correctly within the project.
  * [ ] Document the API usage and any configuration steps for future reference.

### 4. Remove Unused and Deprecated Code

* [ ] **Issue:** There are several commented-out code blocks and unused imports across various files (e.g., `company_news_crew.py` has a commented-out `fact_checker` agent).
* [ ] **Recommendation:**
  * [ ] **Perform a Code Cleanup:** Systematically review all files in `src/` and remove dead code, commented-out blocks, and unused imports. This improves readability and reduces maintenance overhead.
* [ ] **Files:**
  * `src/epic_news/crews/company_news/company_news_crew.py`
  * ... and others.

<!-- ### 1. Eliminate `utils/html` in Favor of Deterministic Rendering

* [ ] **Issue:** The `utils/html` directory contains numerous `*_html_factory.py` files that manually construct HTML. This is brittle and inconsistent with the "Deterministic Python-Based Rendering" pattern described in the architecture guide, which favors `TemplateManager`.
* [ ] **Recommendation:**
  - [ ] **Delete `utils/html`:** Remove the entire `src/epic_news/utils/html` directory.
  - [ ] **Refactor to Use `TemplateManager`:** Modify all crew handlers in `main.py` to pass the Pydantic model output directly to `TemplateManager` for rendering, as demonstrated by the `saint_to_html` example in the documentation. This ensures all HTML generation is centralized and consistent.
* [ ] **Files:**
  * `src/epic_news/utils/html/` (delete entire directory)
  * `src/epic_news/main.py` (update all `generate_*` methods) -->
