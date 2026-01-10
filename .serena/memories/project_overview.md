# Epic News Project Overview

## Project Purpose

Epic News is an all-in-one, natural-language-powered AI assistant for financial analysis, news aggregation, research, recipes, and more. Built on **CrewAI**, it allows users to ask questions in plain English or French, and delegates tasks to specialized teams of AI agents ("crews").

## Core Concept

Users interact with the system using natural language requests. The system uses AI to classify the request and routes it to the appropriate specialized crew. Each crew is a team of AI agents with specific expertise and tools.

## Tech Stack

### Core Framework
- **CrewAI**: Multi-agent AI orchestration framework (Flow paradigm)
- **Python**: 3.10+ (requires >=3.10, <3.13)
- **UV**: Modern, fast package manager for Python (EXCLUSIVE - never use pip/poetry)

### Key Libraries
- **Pydantic**: Data validation and models (v2.7.0+)
- **Loguru**: Advanced logging system
- **Jinja2**: Template engine for HTML rendering
- **WeasyPrint**: HTML to PDF conversion
- **BeautifulSoup4**: HTML parsing and manipulation

### AI & LLM
- **OpenAI API**: Primary LLM provider
- **LangChain**: Community tools and integrations
- **Composio**: Tool integrations for CrewAI

### Data & APIs
- **yfinance**: Yahoo Finance data
- **feedparser**: RSS feed parsing
- **requests**: HTTP client with caching support
- **httpx**: Modern async HTTP client
- **tenacity**: Retry logic for resilient HTTP calls

### Testing & Quality
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking support
- **Faker**: Realistic test data generation
- **pendulum**: Date/time manipulation for tests
- **ruff**: Fast linter and formatter
- **yamllint**: YAML validation
- **pre-commit**: Git hooks for quality checks

### Additional Tools
- **Streamlit**: Web UI (optional)
- **FastAPI**: API server (optional)
- **pandas**: Data manipulation
- **matplotlib/seaborn/scikit-learn**: Data visualization and analysis

## Project Structure

```
epic_news/
├── src/epic_news/           # Main source code
│   ├── crews/               # Crew implementations (25+ specialized crews)
│   │   ├── fin_daily/       # Financial analysis crew
│   │   ├── news_daily/      # Daily news aggregation
│   │   ├── cooking/         # Recipe generation
│   │   ├── legal_analysis/  # Legal document analysis
│   │   └── ...              # Many more specialized crews
│   ├── tools/               # Tool implementations (60+ tools)
│   ├── models/              # Pydantic data models
│   ├── utils/               # Utility functions
│   ├── services/            # Service layer
│   ├── main.py              # Flow orchestration (ReceptionFlow)
│   ├── app.py               # Application setup
│   └── api.py               # API endpoints
├── docs/                    # Comprehensive documentation
├── tests/                   # Unit and integration tests
├── templates/               # Jinja2 HTML templates
├── output/                  # Generated reports (HTML, PDF, YAML)
├── logs/                    # Application logs
├── cache/                   # Cached data
├── db/                      # Database files
├── data/                    # Static data files
├── scripts/                 # Utility scripts
├── .github/                 # GitHub workflows
├── pyproject.toml           # Project configuration
├── .env                     # Environment variables (NOT committed)
└── README.md                # User documentation
```

## Key Crews

The project includes 25+ specialized crews:
- **FinDailyCrew**: Financial portfolio analysis
- **NewsDailyCrew**: Daily news aggregation (7 categories)
- **CompanyNewsCrew**: Company/topic research
- **CookingCrew**: Recipe generation (Thermomix, Paprika format)
- **LegalAnalysisCrew**: Legal document analysis
- **SalesProspectingCrew**: Sales contact research
- **LibraryCrew**: Book summaries and recommendations
- **HolidayPlannerCrew**: Travel planning
- **MenuDesignerCrew**: Menu planning
- **DeepResearchCrew**: In-depth research reports
- **OsintCrew**: Open-source intelligence
- And many more...

## Output Format

Primary output is **professional HTML reports** with:
- UTF-8 encoding
- Proper HTML5 structure
- CSS styling with theme compatibility
- Strategic emoji usage
- Structured sections with clear headings
- Optional PDF export via WeasyPrint

## Configuration

- **Environment Variables**: `.env` file for API keys and configuration
- **YAML Configuration**: Agents and tasks defined in YAML files
- **Code-based Tool Assignment**: Tools assigned programmatically (not in YAML)

## Design Philosophy

- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **DRY**: Don't Repeat Yourself
- **Fail Fast**: Validate early with type hints and Pydantic
- **CrewAI-First**: Use framework capabilities before custom code
- **Configuration-Driven**: Separate code from configuration
- **Async by Default**: Maximize performance with parallel execution
