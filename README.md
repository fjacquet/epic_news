# Epic News Crew

Welcome to Epic News Crew — your all-in-one, natural-language-powered AI assistant for financial analysis, news, research, recipes, and more. Built on [crewAI](https://crewai.com), it’s designed for everyone: just ask in plain English or French, and let the right team of AI agents (“crews”) do the work.

---

## 🚀 Quick Start

1. **Install prerequisites:**
   - Python >=3.10 <3.13
   - [UV](https://docs.astral.sh/uv/) for dependency management

2. **Install dependencies:**

   ```bash
   pip install uv
   crewai install
   ```

3. **Set up your `.env` file:**
   - Add your API keys (see below for details)

4. **Run the app:**

   ```bash
   crewai flow kickoff
   ```

5. **Type your request:**
   - Example: `Give me a daily financial summary of my stocks and crypto.`
   - Or: `Plan a vegetarian dinner for four.`

---

## 🧑‍💻 What Can I Ask? (Use Cases & Prompts)

| What You Want To Do                              | What To Type (Sample Prompt)                                             |
|--------------------------------------------------|--------------------------------------------------------------------------|
| **Get a financial/crypto portfolio report**      | "Give me a daily financial summary of my stocks and crypto."<br>"Analyse mon portefeuille boursier et crypto et donne-moi des recommandations." |
| **Get a comprehensive daily news report**       | "Generate daily news report."<br>"Donne-moi les actualités du jour."<br>"Get the top 10 news for Switzerland, France, Europe and world." |
| **Summarize the latest news**                    | "Summarize the latest tech news."<br>"Give me a report on AI news this week." |
| **Plan a meal or get a recipe**                  | "Plan a vegetarian dinner for four."<br>"Generate a French ratatouille recipe for Paprika app." |
| **Analyze a legal document**                     | "Review this contract for potential risks."<br>"Analyse ce contrat pour les risques." |
| **Find sales contacts**                          | "Find sales contacts at OpenAI in France."                              |
| **Summarize a book or get book suggestions**     | "Summarize 'Le Petit Prince' and suggest similar books."                |
| **Plan a holiday/trip**                          | "Plan a 7-day trip to Japan with cultural and food experiences."        |
| **Write a poem**                                 | "Write a poem about spring in Paris."                                   |
| **Prepare for a meeting**                        | "Prepare for a meeting with the marketing team to discuss Q2 strategy." |
| **Do open-source intelligence (OSINT) research** | "Investigate recent cybersecurity incidents affecting European banks."   |
| **Improve a French marketing message**           | "Améliorer ce message marketing: 'Découvrez notre nouveau produit qui vous aide à gagner du temps.'" |
| **Classify a piece of text**                     | "Classify this text: 'The new iPhone features an improved camera.'"     |
| **Extract the main topic from a request**        | "Extract the main topic: 'I'm interested in learning about Mediterranean diets.'" |
| **Capture info about travelers**                 | "We are a family of four: two adults and two children."                 |
| **Extract travel/event duration**                | "We will be traveling from July 1st to July 14th."                      |

**Tip:** You can ask follow-up questions or combine topics, e.g., "Give me a financial report and a recipe for dinner tonight."

---

## 🤖 How Does It Work?

Just use natural language—no special format needed. The system uses AI to classify your request and send it to the right expert team (“crew”). If your request is unclear, you’ll be asked to clarify.

---

## 🛠️ Features & Crew Directory

Each “crew” is a team of specialized AI agents. Here’s what they do:

### **FinDailyCrew**

- **What:** Analyzes your entire stock and crypto portfolio. Generates a detailed, professional HTML report (in French) with buy/sell/keep recommendations for each asset.
- **Sample prompt:**
  - "Give me a daily financial summary of my stocks and crypto."
  - "Analyse mon portefeuille boursier et crypto et donne-moi des recommandations."
- **Output:** HTML report (French), sent by email if configured.

### **NewsDailyCrew**

- **What:** Collects and curates the top 10 daily news items for 7 categories: Suisse Romande, Suisse, France, Europe, World, Wars, and Economy. Generates a comprehensive French-language news report with deduplication and professional formatting.
- **Sample prompt:**
  - "Generate daily news report."
  - "Donne-moi les actualités du jour."
  - "Get the top 10 news for Switzerland, France, Europe and world."
- **Output:** Professional HTML news report in French, organized by region/category, sent by email if configured.

### **CompanyNewsCrew**

- **What:** Researches and summarizes news topics, using multiple research and fact-checking agents.
- **Sample prompt:**
  - "Summarize the latest tech news."
  - "Give me a report on AI news this week."
- **Output:** Well-structured news report.

### **CookingCrew**

- **What:** Generates recipes (including Thermomix-optimized) in HTML and Paprika 3-compatible YAML format for easy import into the Paprika app.
- **Sample prompt:**
  - "Plan a vegetarian dinner for four."
  - "Generate a French ratatouille recipe for Paprika app."
- **Output:** HTML recipe + Paprika YAML (as email attachment).

### **LegalAnalysisCrew**

- **What:** Analyzes legal documents, contracts, or cases for risks and compliance.
- **Sample prompt:**
  - "Review this contract for potential risks."
  - "Analyse ce contrat pour les risques."
- **Output:** Legal analysis report.

### **SalesProspectingCrew**

- **What:** Finds and researches sales contacts at target companies.
- **Sample prompt:** "Find sales contacts at OpenAI in France."
- **Output:** List of contacts and research notes.

### **LibraryCrew**

- **What:** Finds books, summarizes them, and suggests similar reads.
- **Sample prompt:** "Summarize 'Le Petit Prince' and suggest similar books."
- **Output:** Book summary and suggestions.

### **HolidayPlannerCrew**

- **What:** Plans holidays and creates detailed travel itineraries.
- **Sample prompt:** "Plan a 7-day trip to Japan with cultural and food experiences."
- **Output:** Travel itinerary.

### **PoemCrew**

- **What:** Writes creative poems on request.
- **Sample prompt:** "Write a poem about spring in Paris."
- **Output:** Poem.

### **MeetingPrepCrew**

- **What:** Prepares for meetings by analyzing objectives and participants.
- **Sample prompt:** "Prepare for a meeting with the marketing team to discuss Q2 strategy."
- **Output:** Meeting prep notes.

### **OsintCrew**

- **What:** Conducts open-source intelligence (OSINT) research and reporting.
- **Sample prompt:** "Investigate recent cybersecurity incidents affecting European banks."
- **Output:** OSINT report.

- **What:** Improves French marketing messages for persuasion and engagement.
- **Sample prompt:** "Améliorer ce message marketing: 'Découvrez notre nouveau produit qui vous aide à gagner du temps.'"
- **Output:** Enhanced marketing copy.

### **Other Crews (Classify, CaptureTopic, CaptureTravelers, CaptureDuration, etc.)**

- **What:** Help with text classification, topic extraction, traveler info, and more.
- **Sample prompt:** See table above.

---

## ⚙️ Installation & Setup

1. **Install Python and UV:**
   - Python >=3.10 <3.13
   - [UV](https://docs.astral.sh/uv/): `pip install uv`
2. **Install dependencies:**
   - `crewai install`
3. **System dependencies for PDF (WeasyPrint):**
   - **macOS:** `brew install pango cairo libffi gdk-pixbuf fontconfig`
   - **Linux:** `sudo apt-get install python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`
   - **Windows:** See [WeasyPrint docs](https://doc.weasyprint.org/stable/first_steps.html#windows)
4. **Set up your `.env` file:**
   - Copy `.env.example` to `.env`
   - Add your API keys: `OPENAI_API_KEY`, `KRAKEN_API_KEY`, `KRAKEN_API_SECRET`, etc.
   - See `.env.example` for details.

---

## ▶️ Running the Project

- **Start the main flow:**

  ```bash
  crewai flow kickoff
  ```

- **Outputs:**
  - Reports are saved in the `output/` directory (HTML, PDF, YAML, etc.).
  - Some crews (like FinDailyCrew) can also send reports by email if configured.

---

## 🧑‍🔬 Advanced Usage

- **Customizing agents/tasks:**
  - Edit `src/epic_news/crews/*/config/agents.yaml` and `tasks.yaml` to change goals, roles, or add new agents/tasks.
- **Adding your own crew:**
  - Copy an existing crew folder in `src/epic_news/crews/`, adjust agents/tasks, and register it in `main.py`.
- **Integrating new tools:**
  - Add new tools in `src/epic_news/tools/` and wire them up in your crew’s config.
- **Environment variables:**
  - Keep all secrets in `.env` (never commit real API keys!).
  - Web scraper provider selection via `WEB_SCRAPER_PROVIDER` (default: `scrapeninja`; options: `scrapeninja`, `firecrawl`). The app uses `src/epic_news/tools/scraper_factory.py::get_scraper()` to select the provider at runtime.

    Example `.env`:

    ```bash
    # Scraper provider (default is scrapeninja)
    WEB_SCRAPER_PROVIDER=scrapeninja

    # API keys for providers
    RAPIDAPI_KEY=your-rapidapi-key          # required for ScrapeNinja
    FIRECRAWL_API_KEY=your-firecrawl-key    # required if using Firecrawl
    ```

---

## 🧪 Testing

- **Run the full test suite:**

  ```bash
  uv run pytest -q
  ```

- **Run PR-001 tests only (JSON outputs and HTTP resilience):**

  ```bash
  uv run pytest -q tests/tools/test_json_outputs.py tests/tools/test_http_resilience.py
  ```

- **Lint and format:**

  ```bash
  uv run ruff check .
  uv run ruff format .
  ```

What these tests cover:

- JSON output standardization: all tool `_run()` results are JSON strings parseable via `json.loads`.
- HTTP resilience: retries on transient 5xx and no retries on 4xx, using stubbed clients (no live network calls).

## ❓ Troubleshooting & FAQ

- **Wrong crew triggered or partial answer?**
  - Rephrase your request or split it into two sentences.
- **PDF/HTML/YAML output missing?**
  - Check the `output/` directory and your email (if configured).
- **API errors?**
  - Ensure your `.env` file is set up and keys are correct.
- **Still stuck?**
  - See [crewAI docs](https://docs.crewai.com) or open an issue on GitHub.

---

## 📚 Documentation Guide

This project includes comprehensive documentation to help you get started, whether you're a user, developer, or contributor. Here’s a recommended reading order:

1. **`README.md` (This file)**: Provides a high-level overview of the project, its features, and how to get started quickly.
2. **`docs/USE_CASES.md`**: A user-focused guide that showcases all supported use cases with example prompts. It's the best place to discover what you can ask Epic News to do.
3. **`docs/DESIGN_PRINCIPLES.md`**: Essential reading for developers. It outlines the core architectural and coding principles that govern the project, including critical patterns for async execution, tool usage, and output generation.
4. **`docs/tools_handbook.md`**: The definitive guide to all tools available to the AI agents. It details their functionality, parameters, and any required API keys.
5. **`docs/CREWAI_ENGAGEMENT_RULES.md`**: Describes the rules and anti-patterns for using the CrewAI framework within this project, ensuring consistency and adherence to the core architecture.
6. **`docs/output_formatting_guide.md`**: Specifies the standards for all generated reports, particularly the HTML output format.

---

## 🤝 Contributing

- PRs welcome! Please follow code style and add tests where relevant.
- See `CONTRIBUTING.md` if available, or open an issue to discuss big changes.

---

## 📚 Support & Links

- [crewAI documentation](https://docs.crewai.com)
- [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with the docs](https://chatg.pt/DWjSBZn)

---

Let’s create wonders together with the power and simplicity of crewAI!
