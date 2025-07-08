# Project Roadmap & Task List

This document outlines the development roadmap, current tasks, and a history of completed work for the Epic News project.

## 🚀 Next Up (Priority)

- [x] **Refactor `ContentState` Model:** Replace `Union[Any, None]` fields with specific Pydantic models for each crew result to improve type safety and data clarity.
  - **File:** `src/epic_news/models/content_state.py`
- [x] **Standardize Pydantic Optional Fields:** Consistently use `Optional[X]` instead of `Union[X, None]` across all Pydantic models, while avoiding the `|` operator for compatibility.
  - **Files:** `src/epic_news/models/`
- [x] **Relocate `bin` Scripts:** Move helper scripts from `src/epic_news/bin` to a top-level `scripts/` directory to separate them from core application code and improve their quality.
- [x] **Standardize Logging in Streamlit App:** Refactor `app.py` to use `loguru` for logging, ensuring consistency with the rest of the application.
  - **File:** `src/epic_news/app.py`

## 📝 To-Do

### HTML Rendering Integration

- [ ] **Integrate HTML Rendering for OSINT Crews:** Connect the HTML rendering pipeline for the remaining OSINT and other crews.
  - [x] `company_profiler`
  - [x] `cross_reference_report_crew`
  - [x] `geospatial_analysis`
  - [x] `hr_intelligence`
  - [x] `legal_analysis`
  - [ ] `marketing_writers`
  - [x] `menu_designer`
  - [x] `sales_prospecting`
  - [x] `tech_stack`
  - [x] `web_presence`

### Code Cleanup and Maintenance

- [ ] **Remove Unused and Deprecated Code:** Systematically review the `src/` directory to remove commented-out code blocks, unused imports, and other dead code to improve readability and maintainability.
  - **Example File:** `src/epic_news/crews/company_news/company_news_crew.py`

### Containerization

- [ ] **Verify CrewAI Execution in Docker:** Finalize and verify the setup for running CrewAI reliably within a containerized environment.

## 📋 Backlog (Future Tasks)

- [ ] **n8n Integration:**
  - [ ] Connect n8n to retrieve data initiated by CrewAI.
  - [ ] Connect n8n to initiate CrewAI workflows.
- [ ] **Technology Watch Agents:** Create new agents for monitoring and reporting on various technologies (Nutanix, Netbackup, Commvault, etc.).
- [ ] **Free API Integration:** Research, evaluate, and integrate valuable free APIs to expand the project's data-gathering capabilities.

## ✅ Changelog (Completed Tasks)

### Q3 2025

- **Pydantic Model & OSINT Crew Refactoring:**
  - **Structured Outputs:** Refactored 8 OSINT crews (`CompanyProfiler`, `CrossReferenceReport`, `GeospatialAnalysis`, `HRIntelligence`, `LegalAnalysis`, `WebPresence`, `TechStack`) to use Pydantic models for structured, reliable outputs.
  - **Centralized Models:** Relocated all crew-specific Pydantic models to a dedicated `src/epic_news/models/crews/` directory, improving project structure and modularity.
  - **Comprehensive Testing:** Created and validated unit tests for all new and relocated models to ensure data integrity.
  - **Project-Wide Updates:** Updated all import paths across the project to reflect the new model locations and fixed all resulting test failures.

- **HTML Reporting System:**
  - **Cross-Reference Report:** Implemented a complete HTML report generation pipeline for the Cross-Reference Crew, including an HTML factory, a Jinja2 template, and a dynamic regeneration script.
  - **Main Integration:** Integrated the HTML generation logic into the main application entry point.

- **Logging Modernization:**
  - **Loguru Integration:** Replaced the standard `logging` module with `loguru` across the core application for more powerful and configurable logging.
  - **Configuration:** Set up `loguru` sinks for both console and file-based logging.
  - **Documentation:** Updated the development guide to reflect the new logging standards.

- **Advanced Testing Libraries:**
  - **Dependencies:** Integrated `Faker`, `pytest-mock`, and `pendulum` to enhance the testing framework with realistic data generation, mocking, and precise time control.
  - **Standards:** Created sample tests and updated the development guide to establish new testing best practices.

- **Initial Dockerization Setup:**
  - **Dockerfiles:** Created `Dockerfile.api` and `Dockerfile.streamlit` to containerize the application components.
  - **Compose Files:** Set up `docker-compose.yml` files for orchestrating the development and production environments.

- **HTML Rendering for Core Crews:**
  - **Integrated 16 crews** with the HTML rendering pipeline, including `classify`, `company_news`, `cooking`, `fin_daily`, `holiday_planner`, and more.
