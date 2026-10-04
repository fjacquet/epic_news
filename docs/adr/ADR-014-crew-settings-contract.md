# ADR-014: Crew Settings Contract

## Status

Accepted (2026-10-04)

## Context

CrewAI's `Agent`, `Task` and `Crew` are pydantic models that silently drop keyword arguments they do not declare. The 2026-10-04 audit found that most of the project's crew settings had never applied, while `# type: ignore[call-arg]` comments hid the mypy errors that would have flagged them:

- `llm_timeout=` (on agents, crews and tasks) is not a CrewAI field. No LLM had a timeout, so every call used LiteLLM's 600 s default, and the `LLM_TIMEOUT_*` settings did nothing.
- `Crew(max_iter=...)` is not a field. Every agent ran with CrewAI's `Agent.max_iter` default of 25, not the configured 5.
- `Crew(llm_timeout, max_retries, max_retry_limit, respect_context_window)` and `Task(verbose, llm_timeout)` were ignored too.
- Tasks were wired with `agent.copy()`. CrewAI's `LLM.__copy__` does not carry `timeout`, so copied agents ran without one even after the timeout moved to the LLM.
- `deep_research` and `pestel` each hand-built an `MCPServerAdapter`. Only `pestel` stopped it, so `deep_research` leaked a `wikipedia-mcp` subprocess on every run.
- Research agents carried tools their tasks never used (report renderers, PDF and KPI tools, duplicate search tools), and some held crewai's unscoped `FileReadTool` next to web search and scrape tools.

## Decision

- **Timeout on the LLM.** Every agent gets `llm=LLMConfig.get_openrouter_llm(task_type="quick"|"default"|"long")`. The LLM is built with `timeout=LLMConfig.get_timeout(task_type)` (120/300/600 s, from `LLM_TIMEOUT_*`) in `src/epic_news/config/llm_config.py`. `llm_timeout=` is not used anywhere.
- **`max_iter` on each Agent.** Every agent sets `max_iter=LLMConfig.get_max_iter()` (`CREW_MAX_ITER`, default 15). The single override is fin_daily's stock analyst, `max_iter=30` (`src/epic_news/crews/fin_daily/fin_daily.py`), which makes about one tool call per ticker of a 60+ line portfolio CSV. `Crew` keeps only fields it declares, such as `max_rpm=LLMConfig.get_max_rpm()`.
- **No copied agents.** Tasks receive the agent instance (`agent=self.my_agent()`), never `agent.copy()`.
- **Guards in CI.**
  - `tests/crews/test_constructor_kwargs.py` parses `src/epic_news` with `ast` and fails on any keyword passed to `Agent(`, `Task(` or `Crew(` that is not a declared model field or alias.
  - `tests/crews/test_agent_settings_contract.py` builds every crew in `tests/crews/_registry.py` (no LLM calls). It asserts that each agent's LLM has a timeout, that `max_iter` matches `LLMConfig.get_max_iter()` or the documented `MAX_ITER_OVERRIDES` table, that no agent holds the same tool twice, and that no `FileReadTool` sits next to a web search or scrape tool.
  - Type-ignores that only hid invalid kwargs are removed.
- **MCP lifecycle through CrewBase** (`src/epic_news/config/mcp_config.py`).
  - Crews declare `mcp_server_params = MCPConfig.get_wikipedia_mcp()` and take tools through `get_mcp_tools_or_empty(self)`. This wraps CrewBase's `get_mcp_tools()`, which lazily starts one shared adapter per crew instance.
  - A server that cannot start logs a warning and yields `[]`. The failure is remembered on the crew instance, so PESTEL's six researchers make a single start attempt instead of six.
  - CrewBase stops the adapter only in its after-kickoff hook, that is, after a successful kickoff. `ReceptionFlow.generate_deep_research` and `generate_pestel` (`src/epic_news/main.py`) therefore call `close_mcp(crew)` in a `finally` around `kickoff_flow(...)`. `close_mcp` clears the reference before stopping and logs stop errors, so it is safe after the hook and when called twice.
- **Tool hygiene.**
  - Each agent gets only the tools its tasks use.
  - An agent that searches or scrapes the web never also holds crewai's unscoped `FileReadTool`. Agents that must read files use `OutputFileReadTool` (`src/epic_news/tools/output_file_read_tool.py`), which is confined to its `root`: `output/` by default, `data/` for fin_daily's portfolio CSVs (ADR-015).
  - Tool factories with no remaining callers were deleted (`tools/report_tools.py`, `tools/data_centric_tools.py`, `tools/render_report_tool.py`).

## Consequences

- Configured timeouts and iteration caps now actually reach LiteLLM and the agent loop. Runs that previously looped up to 25 iterations stop at 15. Tuning is done through `.env` (`LLM_TIMEOUT_*`, `CREW_MAX_ITER`), not by editing crews.
- A new crew that passes an unknown kwarg, forgets `max_iter`, builds an LLM without a timeout, or pairs `FileReadTool` with web tools fails the test suite. A deliberate `max_iter` exception must be added to `MAX_ITER_OVERRIDES` next to its reason.
- A CrewAI upgrade that renames or removes a field shows up as a test failure, not as a setting that silently stops applying.
- Wikipedia MCP is optional at runtime: when the server is missing the crew still runs, with fewer sources. The subprocess no longer outlives a failed run.
- Smaller tool lists shorten prompts and remove ways for prompt-injected content to read local files.
