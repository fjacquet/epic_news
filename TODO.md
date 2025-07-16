# Project Roadmap & Task List

This document outlines the development roadmap, current tasks, and a history of completed work for the Epic News project.

## 🚀 Next Up (Priority)

*All priority tasks completed! See Changelog for details.*

## 📝 To-Do

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

- **DeepResearchCrew Integration (July 2025):**
  - **Complete 4-Agent Architecture:** Implemented comprehensive DeepResearchCrew with primary_researcher, wikipedia_specialist, content_analyst, and report_generator agents.
  - **Tool Integration:** Integrated SerperDevTool, ScrapeNinjaTool, WikipediaSearchTool, and WikipediaArticleTool for comprehensive internet research.
  - **Pydantic Models:** Created DeepResearchReport with nested ResearchSource and ResearchSection models for structured output.
  - **Main Flow Integration:** Added DEEPRESEARCH classification and routing in main.py with proper state management.
  - **HTML Rendering:** Implemented DeepResearchRenderer and HTML factory for professional French report generation.
  - **Configuration-Driven:** Updated agents.yaml and tasks.yaml with French language roles, goals, and async execution support.
  - **Template System:** Integrated with universal template system and RendererFactory for consistent HTML output.

- **Menu Designer Integration & Recipe Generation (July 2025):**
  - **End-to-End Workflow:** Successfully implemented complete menu planning to recipe generation integration with 30 recipes generated from weekly menu plans.
  - **Menu Parser Fix:** Updated `MenuGenerator.parse_menu_structure()` to handle new 'dishes' array format while maintaining backward compatibility with old starter/main_course/dessert structure.
  - **Recipe Generation:** Fixed CookingCrew template variable issues (patrika_file, output_file) enabling generation of both JSON and YAML recipe formats.
  - **HTML Rendering:** Fixed MenuRenderer to properly extract and display actual dish names from JSON menu structure instead of generic placeholders.
  - **Production Ready:** Complete integration now processes all dishes from validated weekly menu plans and generates individual recipes with proper file naming.

- **Comprehensive Test Quality Assurance (July 2025):**
  - **Test Suite Excellence:** Achieved 461 tests passing with only 5 skipped, zero failures across the entire project.
  - **Coverage & Quality:** Generated comprehensive test coverage reports and maintained high code quality standards.
  - **Bug Documentation:** Created detailed bug reports and systematic QA processes following project development principles.
  - **Test Infrastructure:** Enhanced test reliability with proper fixtures, mocking, and cross-platform compatibility.
  - **Lint & Format:** All code passes Ruff formatting and linting checks with zero issues.

- **Project Structure & Code Quality Improvements (Q3 2025):**
  - **ContentState Model Refactoring:** Replaced `Union[Any, None]` fields with specific Pydantic models for improved type safety and data clarity.
  - **Pydantic Standardization:** Consistently used `Optional[X]` instead of `Union[X, None]` across all models for better compatibility.
  - **Script Organization:** Relocated helper scripts from `src/epic_news/bin` to top-level `scripts/` directory for better separation of concerns.
  - **Logging Consistency:** Standardized `app.py` to use `loguru` for consistent logging across the entire application.

- **Complete HTML Rendering Integration (Q3 2025):**
  - **OSINT Crews Integration:** Successfully connected HTML rendering pipeline for all 9 OSINT and specialized crews.
  - **Crew Coverage:** Integrated `company_profiler`, `cross_reference_report_crew`, `geospatial_analysis`, `hr_intelligence`, `legal_analysis`, `menu_designer`, `sales_prospecting`, `tech_stack`, and `web_presence`.
  - **Unified Reporting:** All crews now generate consistent, professional HTML reports with proper styling and data presentation.

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
