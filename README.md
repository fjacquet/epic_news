# Epic News Crew

Welcome to the Epic News Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```

### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**
**Add your `COMPOSIO_API_KEY` into the `.env` file**

- Modify `src/epic_news/config/agents.yaml` to define your agents
- Modify `src/epic_news/config/tasks.yaml` to define your tasks
- Modify `src/epic_news/crew.py` to add your own logic, tools and specific args
- Modify `src/epic_news/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your flow and begin execution, run this from the root folder of your project:

```bash
crewai flow kickoff
```

This command initializes the epic-news Flow as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The epic-news Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Crew Directory

Below is a summary of all specialized crews available in this project. Each includes an example of a valid call or input:

### ReceptionCrew
Routes user requests to the appropriate specialized crew based on the input. Acts as the entry point and dispatcher for the system.

**Example:**
```text
"I want to plan a holiday and need a detailed itinerary."
```

### NewsCrew
Monitors and researches news topics, producing comprehensive reports using multiple research and fact-checking agents.

**Example:**
```text
"Give me a report on the latest advancements in renewable energy."
```

### CookingCrew
Creates professional, comprehensive recipes (including Thermomix-optimized when relevant) in both HTML and Paprika 3-compatible YAML formats. Recipes are suitable for direct import into the Paprika app.

**Example:**
```text
"Generate a French ratatouille recipe for Paprika app."
```

### LibraryCrew
Finds books and generates book summaries, leveraging search tools and compositional reasoning.

**Example:**
```text
"Summarize 'Le Petit Prince' and suggest similar books."
```

### FindContactsCrew
Identifies and researches sales contacts at target companies, using a combination of research agents and search tools.

**Example:**
```text
"Find sales contacts at OpenAI in France."
```

### FindLocationCrew
Analyzes user requirements to recommend suitable locations, combining requirements analysis and research agents.

**Example:**
```text
"Suggest a family-friendly vacation spot in Italy."
```

### HolidayPlannerCrew
Plans holidays and creates detailed travel itineraries, including research on destinations, activities, and logistics.

**Example:**
```text
"Plan a 7-day trip to Japan with cultural and food experiences."
```

### PoemCrew
Generates creative poems on request, using a specialized poem-writing agent.

**Example:**
```text
"Write a poem about spring in Paris."
```

### MeetingPrepCrew
Prepares for meetings by analyzing context, objectives, and participants, and generating relevant preparation materials.

**Example:**
```text
"Prepare for a meeting with the marketing team to discuss Q2 strategy."
```

### OsintCrew
Conducts open-source intelligence (OSINT) research and reporting, useful for investigations and information gathering.

**Example:**
```text
"Investigate recent cybersecurity incidents affecting European banks."
```

### MarketingWritersCrew
Enhances French marketing messages to make them more persuasive and engaging for potential customers, using specialized marketing and copywriting expertise.

**Example:**
```text
"Améliorer ce message marketing: 'Découvrez notre nouveau produit qui vous aide à gagner du temps.'"
```

### ClassifyCrew
Classifies user content into predefined categories using a classification agent and task.

**Example:**
```text
"Classify this text: 'The new iPhone features an improved camera.'"
```

### CaptureTopicCrew
Extracts the main topic from a user request, providing structured topic information for downstream crews.

**Example:**
```text
"Extract the main topic: 'I'm interested in learning about Mediterranean diets.'"
```

### CaptureTravelersCrew
Captures information about travelers from user input, supporting travel planning and logistics.

**Example:**
```text
"We are a family of four: two adults and two children."
```

### CaptureDurationCrew
Extracts travel duration or event timing from user input, assisting other crews with scheduling and planning.

**Example:**
```text
"We will be traveling from July 1st to July 14th."
```

## Cooking Crew: Paprika 3-Compatible Recipes

When you generate a recipe with the Cooking Crew, the system will produce:
- An HTML recipe file for easy reading and sharing
- **A Paprika 3-compatible YAML file as an email attachment**

This YAML file can be imported directly into the Paprika recipe management app, making it easy to build your digital cookbook with structured, app-ready recipes.

The Paprika YAML attachment is automatically included when you request a recipe, ensuring seamless integration with Paprika 3 and similar recipe apps.

## Support

For support, questions, or feedback regarding the {{crew_name}} Crew or crewAI.

- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
