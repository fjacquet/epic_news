# To-Do

## 🔥 Next Up (Priority)

* [ ] **Refactor Logging to use Loguru**
  * [x] Add `loguru` to `pyproject.toml`.
  * [x] Replace the standard `logging` module with `loguru` across the application.
  * [ ] Configure `loguru` sinks for console and file logging.
  * [ ] Update the development guide with the new logging standards.
  
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
