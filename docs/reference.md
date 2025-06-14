# epic_news Technical Reference

This document provides a technical reference for the epic_news project, covering its architecture, components, and advanced features.

## Project Architecture

epic_news is built on the [CrewAI](https://github.com/joaomdmoura/crewai) framework and follows a modular architecture designed for extensibility and maintainability.

- **Crews**: The core of the application. Each crew is a specialized team of AI agents designed to perform a specific type of financial analysis (e.g., Crypto, Stocks, ETFs).
- **Agents**: The individual AI workers within a crew. Each agent has a specific role, goal, and set of tools. Agent configurations are defined in `agents.yaml` files.
- **Tasks**: The specific assignments for agents. Tasks define the work to be done, the expected output, and which agent should perform it. Task configurations are defined in `tasks.yaml` files.
- **Tools**: The functions and APIs that agents can use to perform their tasks. This includes web search tools, data scraping tools, and financial data APIs.
- **Flow**: The `crewai.flow` orchestrates the execution of the different crews in a predefined sequence.

## Crews

epic_news includes the following pre-configured crews:

### 1. Crypto Crew

- **Objective**: To analyze the cryptocurrency market.
- **Tasks**: Performs technical analysis, risk assessment, and develops investment strategies for specified cryptocurrencies.
- **Output**: A detailed report in HTML and PDF formats on the analyzed digital asset.

### 2. Stock Crew

- **Objective**: To research and analyze publicly traded stocks.
- **Tasks**: Conducts market analysis, screens stocks based on predefined criteria, performs technical analysis, and assesses risk.
- **Output**: A report in HTML and PDF formats on promising stock investment opportunities.

### 3. ETF Crew

- **Objective**: To analyze Exchange-Traded Funds (ETFs).
- **Tasks**: Analyzes market trends, screens for suitable ETFs, and assesses risk factors.
- **Output**: A report in HTML and PDF formats with investment strategies for ETFs.

## Customization

You can easily customize epic_news by modifying the YAML configuration files located in each crew's directory (`src/epic_news/crews/<crew_name>/config/`).

- **To modify an agent**: Edit the `agents.yaml` file. You can change an agent's `role`, `goal`, `backstory`, or assigned `tools`.
- **To modify a task**: Edit the `tasks.yaml` file. You can change a task's `description`, `expected_output`, or the `agent` assigned to it.

## Asynchronous Task Execution

To enhance performance, epic_news utilizes asynchronous execution for I/O-bound tasks, such as calling external APIs or scraping websites.

### How it Works

Tasks that can run concurrently without waiting for each other are marked with `async_execution=True` in their respective crew definition files (e.g., `src/epic_news/crews/stock_crew/stock_crew.py`). This allows CrewAI to run these tasks in parallel, significantly reducing the total execution time.

### Important Constraint

When using a `Process.sequential` workflow in CrewAI, there is a key limitation:

> **The final task in a sequential crew must be synchronous.**

This means the last task in the sequence cannot have `async_execution=True`. All preceding tasks can be asynchronous. epic_news's crews are configured to adhere to this rule to ensure the workflow runs correctly. If you modify the task sequence or add new tasks, ensure the final task remains synchronous.

## Available Tools

The agents in epic_news are equipped with a variety of tools to perform their research, including:

- `SerperDevTool`: For general web searches.
- `FirecrawlScrapeWebsiteTool`: For scraping content from websites.
- `FirecrawlSearchTool`: For searching within a website's content.
- `YoutubeVideoSearchTool`: For finding relevant videos on YouTube.
- `YahooFinanceNewsTool`: For fetching financial news.
- And other specialized financial data tools.
