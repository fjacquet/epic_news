# crewai-custom-tools v0.3.0 Upstream Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `crewai_custom_tools` a true behavioral superset for epic_news by fixing exactly two tools (`SaveToRagTool` constructor injection, `UnifiedRssTool` full pipeline), then release it as git tag `v0.3.0`.

**Architecture:** This plan is executed **inside the separate package repo** `/Users/fjacquet/Projects/crewai_custom_tools` (branch `main`, remote `https://github.com/fjacquet/crewai-custom-tools.git`). It implements **only Workstream 1** of the migration spec. `SaveToRagTool` gains an optional `rag_tool` field + `__init__` so callers inject a pre-configured `crewai_tools.RagTool`; `UnifiedRssTool` regains the `(opml_file_path, days, output_file_path)` signature, `RssFeeds` JSON file-writing, article content-scraping (via the in-package `UnifiedScraperTool`, optional Newspaper3k fast path), and invalid-source tracking. Consumers install this tag via `git+https://github.com/fjacquet/crewai-custom-tools.git@v0.3.0`.

**Tech Stack:** Python >=3.11 (CI matrix 3.11/3.12/3.13), crewai (`crewai.tools.BaseTool`), pydantic v2, feedparser, defusedxml, python-dateutil, pytest + pytest-mock (offline/mocked), hatchling build backend, uv package manager, git-tag release (no PyPI/Docker publish — the tag itself is the artifact).

## Global Constraints

- Work only in the package repo `/Users/fjacquet/Projects/crewai_custom_tools`; never edit epic_news files and never add an epic_news import (the package must not depend on `epic_news.rag_config` or `epic_news.models`).
- Package management is **uv only**: `uv run pytest`, `uv add <pkg>`; never `pip`/`poetry`.
- All tests are **offline/mocked** — no live network. Use the pytest-mock `mocker` fixture and `tmp_path`; mock `feedparser.parse`, `requests.*`, and `sys.modules` as the existing suite does. There is no `conftest.py`.
- Every tool `_run` returns the canonical `{"success", "data", "error"}` JSON envelope via `ok()` / `err()` from `crewai_custom_tools.core.results`; API-backed `_run` methods keep the `@api_tool(provider=..., endpoint=...)` decorator from `crewai_custom_tools.core.decorators`.
- Preserve ADR-0002 (Universal Monolith): no compile-heavy C-extension hard dependencies. Newspaper3k stays an **optional, best-effort** lazy import; the guaranteed scraper path is the pure-Python in-package `UnifiedScraperTool`.
- Stage files explicitly in `git add` (never `git add -A`).
- Every commit message ends with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## Reference facts (verified against the code — do not re-derive)

- Consumer contract (epic_news `src/epic_news/utils/rss_utils.py`) calls the tool **positionally**: `rss_tool._run(opml_file_path, days, output_file_path)`. The function returns `None`; **the written JSON file is the real output.** `main.py:415` calls it with `days` defaulting to 7 and does not pass an invalid-sources path.
- The written JSON must match epic_news's `RssFeeds` schema exactly: `{"rss_feeds": [{"feed_url": str, "articles": [{"title","link","published","summary","content"}]}]}` (epic_news reads it in `RssWeeklyCrew`). We replicate these models **inside the package** (no cross-repo import).
- epic_news injects the RAG tool as `SaveToRagTool(rag_tool=rag_tool)` (`src/epic_news/tools/rag_tools.py:36`); the injected `RagTool` is bound to the correct chromadb collection/embeddings.
- The pydantic private-attr pattern below (`rag_tool: Any = None` field + `self._rag_tool = rag_tool`) is **verified to work** on this package's `crewai.tools.BaseTool` — the injected value is readable in `_run` and defaults to `None`.
- Existing package tests that touch these tools: `tests/test_enterprise_tools.py` (`test_save_to_rag_success`, `test_save_to_rag_failure_returns_error` — both must keep passing), and `tests/test_misc_tools.py` (`test_unified_rss_tool` — **obsolete, delete it**; `test_unified_rss_tool_bad_opml` — **still valid, keep it**; `test_rss_feed_tool_*` — untouched, `RSSFeedTool` is unchanged). The version test lives in `tests/test_scaffold.py`.
- CI (`.github/workflows/ci.yml`) runs the pytest matrix on push/PR to `main` **only** — there is no publish-on-tag or Docker job. "Release" = push `main` (CI runs) + push the `v0.3.0` tag + create a GitHub release. epic_news pins the tag directly.

---

## Task 1: SaveToRagTool optional `rag_tool` constructor injection

**Files:**
- Modify: `src/crewai_custom_tools/enterprise/rag_tools.py`
- Test: `tests/test_enterprise_tools.py` (add one test; keep the two existing SaveToRag tests green)

**Interfaces:**
- Consumes: `ok` from `crewai_custom_tools.core.results`; `api_tool` from `crewai_custom_tools.core.decorators`; `crewai_tools.RagTool` (lazy, only when no tool injected).
- Produces: `SaveToRagTool(rag_tool: Any = None, **kwargs)` — a `crewai.tools.BaseTool` with `name="save_to_rag"`, `args_schema=SaveToRagInput`, and `_run(self, text: str) -> str` returning `ok({"stored": True, "preview": text[:100]})`. epic_news calls `SaveToRagTool(rag_tool=<configured crewai_tools.RagTool>)`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_enterprise_tools.py` (after `test_save_to_rag_failure_returns_error`):

```python
def test_save_to_rag_uses_injected_rag_tool(mocker):
    """An injected rag_tool is used directly, without importing crewai_tools at all."""
    # Force `from crewai_tools import RagTool` to fail — if the injected tool is honored,
    # the import is never reached, so storage still succeeds.
    mocker.patch.dict("sys.modules", {"crewai_tools": None})
    injected = mocker.MagicMock()

    payload = _envelope(SaveToRagTool(rag_tool=injected)._run(text="Acme PESTEL results"))

    assert payload["success"] is True
    assert payload["data"]["stored"] is True
    injected.add.assert_called_once_with("Acme PESTEL results", data_type="text")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_enterprise_tools.py::test_save_to_rag_uses_injected_rag_tool -v`
Expected: FAIL — constructing `SaveToRagTool(rag_tool=injected)` raises a pydantic error because `rag_tool` is not yet an accepted field/argument.

- [ ] **Step 3: Write minimal implementation** — replace the entire contents of `src/crewai_custom_tools/enterprise/rag_tools.py` with:

```python
"""RAG Vector database search and persistence tools."""

import logging
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_custom_tools.core.decorators import api_tool
from crewai_custom_tools.core.results import ok

logger = logging.getLogger(__name__)


class SaveToRagInput(BaseModel):
    """Input schema for SaveToRagTool."""

    text: str = Field(
        ...,
        description="The arbitrary text chunk to store in the project knowledge base RAG vector database.",
    )


class SaveToRagTool(BaseTool):
    """A tool to store research, snippets, or reports directly in a local vector database."""

    name: str = "save_to_rag"
    description: str = "Persist arbitrary text chunks so they can be retrieved and searched later via RAG query tools."
    args_schema: type[BaseModel] = SaveToRagInput
    # Optional pre-configured crewai_tools.RagTool supplied by the caller (see __init__).
    rag_tool: Any = None

    def __init__(self, rag_tool: Any = None, **kwargs: Any) -> None:
        """Accept an optional pre-configured ``RagTool`` bound to the caller's collection.

        The caller (e.g. epic_news's ``get_rag_tools``) supplies a ``RagTool`` wired to the
        correct chromadb collection/embeddings; without it we fall back to a bare default
        ``RagTool()`` at call time. We keep the value on the private ``_rag_tool`` attribute
        so it is never subject to pydantic field validation.
        """
        super().__init__(**kwargs)
        self._rag_tool = rag_tool

    @api_tool(provider="RAG", endpoint="StoreText")
    def _run(self, text: str) -> str:
        """Add a text block to the injected (or default) local vector database.

        Any failure (missing backend, import error, add() error) propagates to
        @api_tool and becomes an error envelope — we never report a fake success (H8).
        """
        rag_tool = self._rag_tool
        if rag_tool is None:
            from crewai_tools import RagTool

            rag_tool = RagTool()
        rag_tool.add(text, data_type="text")
        return ok({"stored": True, "preview": text[:100]})
```

- [ ] **Step 4: Run the SaveToRag tests to verify they pass**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_enterprise_tools.py -k save_to_rag -v`
Expected: PASS — 3 tests: `test_save_to_rag_success` (default path lazily imports the mocked `RagTool`), `test_save_to_rag_failure_returns_error` (import forced to `None` → error envelope), and the new `test_save_to_rag_uses_injected_rag_tool`.

- [ ] **Step 5: Commit**

```bash
cd /Users/fjacquet/Projects/crewai_custom_tools
git add src/crewai_custom_tools/enterprise/rag_tools.py tests/test_enterprise_tools.py
git commit -m "fix(rag): inject optional configured RagTool into SaveToRagTool" \
  -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: UnifiedRssTool — output-file signature, RssFeeds models, JSON file writing

**Files:**
- Create: `src/crewai_custom_tools/tools/web/rss_models.py`
- Modify: `src/crewai_custom_tools/tools/web/rss_aggregator.py` (import block + `UnifiedRssToolInput` + `UnifiedRssTool`; leave `RSSFeedTool` and `_RSS_SOURCES` untouched)
- Modify: `pyproject.toml` (repo root) dependency list — add `python-dateutil`
- Create: `tests/test_rss_aggregator.py`
- Modify: `tests/test_misc_tools.py` (delete the obsolete `test_unified_rss_tool`; keep `test_unified_rss_tool_bad_opml`)

**Interfaces:**
- Consumes: `OpmlParserTool` from `crewai_custom_tools.tools.web.rss`; `err`/`ok` from `crewai_custom_tools.core.results`; `feedparser`, `dateutil.parser`.
- Produces:
  - `Article`, `FeedWithArticles`, `RssFeeds` pydantic models in `crewai_custom_tools.tools.web.rss_models` (field-identical to epic_news's `models/rss_models.py`).
  - `UnifiedRssTool._run(self, opml_file_path: str, days: int = 7, output_file_path: str | None = None, invalid_sources_file_path: str | None = None) -> str`. When `output_file_path` is set, writes `RssFeeds.model_dump()` JSON there. Returns `ok({"feeds": int, "articles": int, "invalid_sources": list[str], "output_file_path": str | None})`.
  - Helper `_fetch_and_filter_articles(self, feed_url, cutoff_date, invalid_sources) -> list[Article]` and static `_entry_pub_date(entry) -> datetime | None`. `_scrape_article_content(self, url) -> str | None` exists as a stub returning `None` here (real body added in Task 3).

- [ ] **Step 1: Add the pure-Python date dependency (ADR-0002 safe)**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv add "python-dateutil>=2.8.0"`
Expected: `pyproject.toml` gains `python-dateutil>=2.8.0` under `[project].dependencies` and `uv.lock` updates. (It is already present transitively via pandas; this makes it explicit and reproducible.)

- [ ] **Step 2: Create the RSS output models** — write `src/crewai_custom_tools/tools/web/rss_models.py`:

```python
"""Pydantic models describing the aggregated RSS output written by ``UnifiedRssTool``.

The JSON shape here is the cross-repo contract consumed by epic_news's RSS weekly
pipeline (``utils/rss_utils.py`` writes the file, ``RssWeeklyCrew`` reads it), so the
field names must stay in lockstep with epic_news's ``models/rss_models.py``.
"""

from __future__ import annotations

from pydantic import BaseModel


class Article(BaseModel):
    """A single article extracted from an RSS feed."""

    title: str
    link: str
    published: str
    summary: str | None = None
    content: str | None = None


class FeedWithArticles(BaseModel):
    """A single RSS feed and its list of recent articles."""

    feed_url: str
    articles: list[Article]


class RssFeeds(BaseModel):
    """A collection of RSS feeds, each with its recent articles."""

    rss_feeds: list[FeedWithArticles]
```

- [ ] **Step 3: Write the failing tests** — write `tests/test_rss_aggregator.py`:

```python
"""Offline tests for the UnifiedRssTool OPML -> RssFeeds JSON pipeline."""

import json
from datetime import datetime, timedelta

from crewai_custom_tools.tools.web.rss_aggregator import UnifiedRssTool

_OPML = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <body>
    <outline text="AI Feed" type="rss" xmlUrl="https://rss.example/ai" htmlUrl="https://rss.example"/>
  </body>
</opml>"""


def _make_feed(mocker, *, recent: bool):
    """Build a MagicMock feedparser feed with a single dated entry."""
    feed = mocker.MagicMock()
    feed.bozo = False
    feed.status = 200
    entry = mocker.MagicMock()
    entry.get.side_effect = lambda key, default=None: {
        "title": "Recent AI News",
        "link": "https://rss.example/ai/1",
        "summary": "A short RSS summary.",
    }.get(key, default)
    when = datetime.now() - timedelta(days=1 if recent else 400)
    entry.published_parsed = when.timetuple()
    feed.entries = [entry]
    return feed


def test_unified_rss_writes_json_file(tmp_path, mocker):
    """When output_file_path is given, the RssFeeds JSON is written to it."""
    opml_file = tmp_path / "feeds.opml"
    opml_file.write_text(_OPML)
    out_file = tmp_path / "sub" / "report.json"  # nested dir must be created
    mocker.patch("feedparser.parse", return_value=_make_feed(mocker, recent=True))

    result = UnifiedRssTool()._run(
        opml_file_path=str(opml_file), days=7, output_file_path=str(out_file)
    )

    assert json.loads(result)["success"] is True
    assert out_file.exists()
    written = json.loads(out_file.read_text())
    assert list(written.keys()) == ["rss_feeds"]
    feed = written["rss_feeds"][0]
    assert feed["feed_url"] == "https://rss.example/ai"
    article = feed["articles"][0]
    assert article["title"] == "Recent AI News"
    assert article["link"] == "https://rss.example/ai/1"
    # No scraper yet (stub returns None) -> content falls back to the RSS summary.
    assert article["content"] == "A short RSS summary."


def test_unified_rss_positional_signature_matches_consumer(tmp_path, mocker):
    """rss_utils calls ._run(opml, days, output) positionally — that contract must hold."""
    opml_file = tmp_path / "feeds.opml"
    opml_file.write_text(_OPML)
    out_file = tmp_path / "report.json"
    mocker.patch("feedparser.parse", return_value=_make_feed(mocker, recent=True))

    UnifiedRssTool()._run(str(opml_file), 7, str(out_file))  # exact positional call
    assert out_file.exists()


def test_unified_rss_filters_old_articles(tmp_path, mocker):
    """Entries older than `days` are dropped; the written feed list is then empty."""
    opml_file = tmp_path / "feeds.opml"
    opml_file.write_text(_OPML)
    out_file = tmp_path / "report.json"
    mocker.patch("feedparser.parse", return_value=_make_feed(mocker, recent=False))

    payload = json.loads(UnifiedRssTool()._run(str(opml_file), 7, str(out_file)))
    assert payload["success"] is True
    assert payload["data"]["feeds"] == 0
    assert json.loads(out_file.read_text())["rss_feeds"] == []
```

- [ ] **Step 4: Run the new tests to verify they fail**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_rss_aggregator.py -v`
Expected: FAIL — the current `UnifiedRssTool._run` signature is `(opml_file_path, days=7, max_articles=50)`, does not write a file, and `rss_models` does not exist / is not used.

- [ ] **Step 5: Replace the import block** in `src/crewai_custom_tools/tools/web/rss_aggregator.py`.

Old:

```python
import json
import math
from typing import ClassVar

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_custom_tools.core.results import err, ok
from crewai_custom_tools.tools.web.rss import OpmlParserTool, RssFeedParserTool
```

New:

```python
import json
import logging
import math
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

import feedparser
from crewai.tools import BaseTool
from dateutil import parser as date_parser
from pydantic import BaseModel, Field, PrivateAttr

from crewai_custom_tools.core.results import err, ok
from crewai_custom_tools.tools.web.rss import OpmlParserTool, RssFeedParserTool
from crewai_custom_tools.tools.web.rss_models import Article, FeedWithArticles, RssFeeds
from crewai_custom_tools.tools.web.scraper import UnifiedScraperTool

logger = logging.getLogger(__name__)
```

- [ ] **Step 6: Replace the `UnifiedRssToolInput` + `UnifiedRssTool` classes** (the block from `class UnifiedRssToolInput(BaseModel):` to the end of the file) with:

```python
class UnifiedRssToolInput(BaseModel):
    """Input schema for UnifiedRssTool."""

    opml_file_path: str = Field(..., description="Path to an OPML file listing RSS feed sources.")
    days: int = Field(7, ge=1, description="Number of past days of entries to include per feed.")
    output_file_path: str | None = Field(
        None,
        description="Optional path to write the aggregated RssFeeds JSON. When set, the written file is the primary output.",
    )
    invalid_sources_file_path: str | None = Field(
        None,
        description="Optional path to write the list of feeds that errored or yielded no articles.",
    )


class UnifiedRssTool(BaseTool):
    """Parse an OPML file end to end: extract feeds, fetch and date-filter entries, scrape
    article content, and (optionally) persist the aggregated result as a RssFeeds JSON file."""

    name: str = "unified_rss_tool"
    description: str = (
        "Process an OPML subscription file end to end: extract every RSS feed URL, fetch each "
        "feed's recent entries, scrape article content, and aggregate them. When an output file "
        "path is provided the RssFeeds JSON is written to it (the file is the primary output)."
    )
    args_schema: type[BaseModel] = UnifiedRssToolInput
    _scraper: Any = PrivateAttr(default=None)

    def _get_scraper(self) -> Any:
        """Lazily build the resilient in-package scraper, reused across articles."""
        if self._scraper is None:
            self._scraper = UnifiedScraperTool()
        return self._scraper

    def _run(
        self,
        opml_file_path: str,
        days: int = 7,
        output_file_path: str | None = None,
        invalid_sources_file_path: str | None = None,
    ) -> str:
        """Parse the OPML, fetch/filter/scrape entries per feed, and aggregate or persist them."""
        opml_payload = json.loads(OpmlParserTool()._run(opml_file_path=opml_file_path))
        if not opml_payload["success"]:
            return err(opml_payload["error"])

        feed_urls = opml_payload["data"]
        invalid_sources: set[str] = set()
        # Inclusive, day-granular cutoff: normalise to 00:00 so any hour that day is kept.
        cutoff_date = (datetime.now() - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        all_feeds: list[FeedWithArticles] = []
        for feed_url in feed_urls:
            articles = self._fetch_and_filter_articles(feed_url, cutoff_date, invalid_sources)
            if articles:
                all_feeds.append(FeedWithArticles(feed_url=feed_url, articles=articles))
            else:
                invalid_sources.add(feed_url)

        # Scrape content for each article, falling back to the RSS summary on failure.
        for feed in all_feeds:
            for article in feed.articles:
                scraped = self._scrape_article_content(article.link)
                if scraped:
                    article.content = scraped
                elif article.summary:
                    article.content = article.summary

        rss_feeds = RssFeeds(rss_feeds=all_feeds)

        if output_file_path:
            output_dir = os.path.dirname(output_file_path)
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            with open(output_file_path, "w", encoding="utf-8") as fh:
                json.dump(rss_feeds.model_dump(), fh, ensure_ascii=False, indent=2)
            logger.info(f"UnifiedRssTool wrote {len(all_feeds)} feeds to {output_file_path}")

        total_articles = sum(len(f.articles) for f in all_feeds)
        return ok(
            {
                "feeds": len(all_feeds),
                "articles": total_articles,
                "invalid_sources": sorted(invalid_sources),
                "output_file_path": output_file_path,
            }
        )

    def _fetch_and_filter_articles(
        self, feed_url: str, cutoff_date: datetime, invalid_sources: set[str]
    ) -> list[Article]:
        """Fetch a feed and return Articles newer than ``cutoff_date``; track invalid feeds."""
        try:
            feed = feedparser.parse(feed_url)

            status = getattr(feed, "status", None)
            if status is not None:
                try:
                    if int(status) >= 400:
                        invalid_sources.add(feed_url)
                        return []
                except (TypeError, ValueError):
                    pass  # non-integer status: treat as unknown, keep going

            if getattr(feed, "bozo", False):
                invalid_sources.add(feed_url)
                return []

            articles: list[Article] = []
            for entry in feed.entries:
                pub_date = self._entry_pub_date(entry)
                if not pub_date or pub_date < cutoff_date:
                    continue
                articles.append(
                    Article(
                        title=entry.get("title", "No Title"),
                        link=entry.get("link", ""),
                        published=pub_date.isoformat(),
                        summary=entry.get("summary"),
                        content=None,  # populated by the scraping pass
                    )
                )
            return articles
        except Exception as exc:  # noqa: BLE001 — any feed error marks the source invalid
            logger.warning(f"Error fetching feed {feed_url}: {exc}")
            invalid_sources.add(feed_url)
            return []

    @staticmethod
    def _entry_pub_date(entry: Any) -> datetime | None:
        """Best-effort naive publication date: struct_time fields first, then string fields."""
        for attr in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime(*parsed[:6])
                except (TypeError, ValueError):
                    pass
        for attr in ("published", "updated"):
            value = getattr(entry, attr, None)
            if value:
                try:
                    return date_parser.parse(value).replace(tzinfo=None)
                except (TypeError, ValueError):
                    pass
        return None

    def _scrape_article_content(self, url: str) -> str | None:
        """Stub: real content-scraping body is added in Task 3 (returns None for now)."""
        return None
```

- [ ] **Step 7: Delete the obsolete existing test** in `tests/test_misc_tools.py`.

Remove this function entirely (its contract — mocking `RssFeedParserTool._run` and reading `data.articles` as a list — no longer applies; the rewrite uses `feedparser` directly and reports `data.articles` as an int count). Delete exactly:

```python
def test_unified_rss_tool(mocker):
    mocker.patch(
        "crewai_custom_tools.tools.web.rss_aggregator.OpmlParserTool._run",
        side_effect=lambda *a, **k: ok(["http://feed1", "http://feed2"]),
    )
    mocker.patch(
        "crewai_custom_tools.tools.web.rss_aggregator.RssFeedParserTool._run",
        side_effect=lambda *a, **k: ok([{"title": "A", "link": "l", "published": "p", "summary": ""}]),
    )
    payload = _env(UnifiedRssTool()._run(opml_file_path="/tmp/x.opml"))
    assert payload["success"] is True
    assert payload["data"]["feeds"] == 2
    assert len(payload["data"]["articles"]) == 2
```

Keep `test_unified_rss_tool_bad_opml` (still valid — the `err` short-circuit is unchanged) and both `test_rss_feed_tool_*` (the `RSSFeedTool` class is untouched).

- [ ] **Step 8: Run the new + affected tests to verify they pass**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_rss_aggregator.py tests/test_misc_tools.py -v`
Expected: PASS — the three new `test_rss_aggregator.py` tests, plus `test_unified_rss_tool_bad_opml`, `test_rss_feed_tool_aggregates`, `test_rss_feed_tool_unknown_region`, and the rest of `test_misc_tools.py`; no `test_unified_rss_tool` remains.

- [ ] **Step 9: Commit**

```bash
cd /Users/fjacquet/Projects/crewai_custom_tools
git add pyproject.toml uv.lock \
  src/crewai_custom_tools/tools/web/rss_models.py \
  src/crewai_custom_tools/tools/web/rss_aggregator.py \
  tests/test_rss_aggregator.py tests/test_misc_tools.py
git commit -m "feat(rss): restore UnifiedRssTool output-file signature and RssFeeds models" \
  -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: UnifiedRssTool — content-scraping + invalid-source file writing

**Files:**
- Modify: `src/crewai_custom_tools/tools/web/rss_aggregator.py` (replace the `_scrape_article_content` stub; insert the invalid-sources write block into `_run`)
- Test: `tests/test_rss_aggregator.py` (add two tests)

**Interfaces:**
- Consumes: the in-package `UnifiedScraperTool` (via `self._get_scraper()`), whose `_run(url=...)` returns the `{"success", "data": {"provider","title","content"}, "error"}` envelope; optional `newspaper.Article` (best-effort lazy import).
- Produces: `_scrape_article_content(self, url) -> str | None` returning scraped body text (or `None` so `_run` falls back to the RSS summary); and, when `invalid_sources_file_path` is set and any source was invalid, a JSON file `{"invalid_sources": list[str], "timestamp": str, "total_invalid": int}`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_rss_aggregator.py`:

```python
def test_unified_rss_scrapes_article_content(tmp_path, mocker):
    """A successful scrape populates article.content instead of the RSS summary."""
    opml_file = tmp_path / "feeds.opml"
    opml_file.write_text(_OPML)
    out_file = tmp_path / "report.json"
    mocker.patch("feedparser.parse", return_value=_make_feed(mocker, recent=True))
    # Force Newspaper3k unavailable so the in-package scraper path is exercised.
    mocker.patch.dict("sys.modules", {"newspaper": None})
    mocker.patch(
        "crewai_custom_tools.tools.web.rss_aggregator.UnifiedScraperTool._run",
        return_value=json.dumps(
            {
                "success": True,
                "data": {"provider": "standard", "title": "t", "content": "FULL SCRAPED BODY " * 10},
                "error": None,
            }
        ),
    )

    UnifiedRssTool()._run(str(opml_file), 7, str(out_file))
    article = json.loads(out_file.read_text())["rss_feeds"][0]["articles"][0]
    assert "FULL SCRAPED BODY" in article["content"]
    assert article["content"] != "A short RSS summary."


def test_unified_rss_writes_invalid_sources_file(tmp_path, mocker):
    """A feed returning HTTP >= 400 is recorded in the invalid-sources file."""
    opml_file = tmp_path / "feeds.opml"
    opml_file.write_text(_OPML)
    out_file = tmp_path / "report.json"
    inv_file = tmp_path / "invalid.json"

    bad = mocker.MagicMock()
    bad.bozo = False
    bad.status = 500
    bad.entries = []
    mocker.patch("feedparser.parse", return_value=bad)

    UnifiedRssTool()._run(
        str(opml_file), 7, str(out_file), invalid_sources_file_path=str(inv_file)
    )

    assert inv_file.exists()
    data = json.loads(inv_file.read_text())
    assert "https://rss.example/ai" in data["invalid_sources"]
    assert data["total_invalid"] == 1
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_rss_aggregator.py -k "scrapes_article_content or invalid_sources" -v`
Expected: FAIL — `_scrape_article_content` is still the stub (content stays the summary), and `_run` does not write an invalid-sources file yet.

- [ ] **Step 3: Replace the `_scrape_article_content` stub** in `src/crewai_custom_tools/tools/web/rss_aggregator.py`.

Old:

```python
    def _scrape_article_content(self, url: str) -> str | None:
        """Stub: real content-scraping body is added in Task 3 (returns None for now)."""
        return None
```

New:

```python
    def _scrape_article_content(self, url: str) -> str | None:
        """Scrape readable article text, staying pure-Python-friendly (ADR-0002).

        Order: optional Newspaper3k (only if the caller installed it) -> the in-package
        resilient UnifiedScraperTool (requests + BeautifulSoup, auto-escalating to
        ScrapeNinja/Firecrawl when their keys are set) -> None (caller uses the RSS summary).
        """
        if not url:
            return None

        # 1. Best-effort Newspaper3k — never a hard dependency of this package.
        try:
            from newspaper import Article as NewspaperArticle

            article = NewspaperArticle(url)
            article.download()
            article.parse()
            if article.text and len(article.text.strip()) > 100:
                return str(article.text)
        except Exception as exc:  # noqa: BLE001 — ImportError or any scrape error
            logger.debug(f"Newspaper3k unavailable/failed for {url}: {exc}")

        # 2. Fall back to the package's own resilient scraper.
        try:
            payload = json.loads(self._get_scraper()._run(url=url))
            if payload.get("success"):
                content = (payload.get("data") or {}).get("content")
                if content:
                    return str(content)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"UnifiedScraperTool failed for {url}: {exc}")

        return None
```

- [ ] **Step 4: Insert the invalid-sources write block** into `_run`. Locate this exact region (added in Task 2):

```python
        total_articles = sum(len(f.articles) for f in all_feeds)
        return ok(
```

Replace it with (inserting the block just before `total_articles`):

```python
        if invalid_sources and invalid_sources_file_path:
            inv_dir = os.path.dirname(invalid_sources_file_path)
            if inv_dir:
                Path(inv_dir).mkdir(parents=True, exist_ok=True)
            with open(invalid_sources_file_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "invalid_sources": sorted(invalid_sources),
                        "timestamp": datetime.now().isoformat(),
                        "total_invalid": len(invalid_sources),
                    },
                    fh,
                    ensure_ascii=False,
                    indent=2,
                )
            logger.info(
                f"UnifiedRssTool recorded {len(invalid_sources)} invalid sources to {invalid_sources_file_path}"
            )

        total_articles = sum(len(f.articles) for f in all_feeds)
        return ok(
```

- [ ] **Step 5: Run the RSS tests to verify they pass**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_rss_aggregator.py -v`
Expected: PASS — all five `test_rss_aggregator.py` tests (Task 2's three + these two). The `test_unified_rss_writes_json_file` case still passes because that test injects no scraper mock, so `_get_scraper()._run` makes a real (offline-failing) call, `_scrape_article_content` returns `None`, and content falls back to the summary.

> Note: `test_unified_rss_writes_json_file` (Task 2) does not mock the scraper. With no `RAPIDAPI_KEY`/`FIRECRAWL_API_KEY` and a non-resolvable `rss.example` URL, `UnifiedScraperTool._run` returns an `err` envelope (no exception escapes it), so `_scrape_article_content` returns `None` and the summary-fallback assertion holds. No live network dependency is introduced.

- [ ] **Step 6: Commit**

```bash
cd /Users/fjacquet/Projects/crewai_custom_tools
git add src/crewai_custom_tools/tools/web/rss_aggregator.py tests/test_rss_aggregator.py
git commit -m "feat(rss): scrape article content and persist invalid sources in UnifiedRssTool" \
  -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Release v0.3.0 — version bump, CHANGELOG, tag + GitHub release

**Files:**
- Modify: `tests/test_scaffold.py` (version assertion)
- Modify: `src/crewai_custom_tools/__init__.py` (`__version__`)
- Modify: `pyproject.toml` (`version`)
- Modify: `CHANGELOG.md` (new `[0.3.0]` section)

**Interfaces:**
- Consumes: nothing new.
- Produces: `crewai_custom_tools.__version__ == "0.3.0"`; `pyproject.toml` `version = "0.3.0"`; a `CHANGELOG.md` `[0.3.0]` entry; git tag `v0.3.0` (what epic_news pins via `git+https://github.com/fjacquet/crewai-custom-tools.git@v0.3.0`).

- [ ] **Step 1: Update the version test (make it fail first)** in `tests/test_scaffold.py`.

Old:

```python
    assert crewai_custom_tools.__version__ == "0.2.0"
```

New:

```python
    assert crewai_custom_tools.__version__ == "0.3.0"
```

- [ ] **Step 2: Run the version test to verify it fails**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_scaffold.py::test_version -v`
Expected: FAIL — `AssertionError`, `__version__` is still `"0.2.0"`.

- [ ] **Step 3: Bump `__version__`** in `src/crewai_custom_tools/__init__.py`.

Old:

```python
__version__ = "0.2.0"
```

New:

```python
__version__ = "0.3.0"
```

- [ ] **Step 4: Bump the package version** in `pyproject.toml`.

Old:

```toml
version = "0.2.0"
```

New:

```toml
version = "0.3.0"
```

- [ ] **Step 5: Run the version test to verify it passes**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest tests/test_scaffold.py::test_version -v`
Expected: PASS.

- [ ] **Step 6: Add the CHANGELOG entry** — insert directly beneath the `---` on line 5 of `CHANGELOG.md` (above `## [0.2.0] - 2026-07-08`):

```markdown
## [0.3.0] - 2026-07-08

### Fixed

- **`SaveToRagTool` collection injection**: the tool now accepts an optional pre-configured
  `rag_tool` via its constructor (`SaveToRagTool(rag_tool=...)`) and stores into it, instead of
  always instantiating a bare default `RagTool()` — which wrote to the wrong chromadb
  collection/embeddings and silently broke save->retrieve. Falls back to a default `RagTool()`
  only when none is injected. Keeps the `save_to_rag` name, args schema, and
  `{success,data,error}` envelope.
- **`UnifiedRssTool` full-pipeline restoration**: restored the
  `_run(opml_file_path, days=7, output_file_path=None, invalid_sources_file_path=None)`
  signature, `RssFeeds` JSON **output-file writing**, article **content-scraping** (via the
  in-package resilient `UnifiedScraperTool`, with an optional Newspaper3k fast path), and
  **invalid-source tracking**. This makes the tool a drop-in for programmatic callers that
  invoke `._run(opml, days, output_file_path)` positionally and rely on the written file as the
  output.

### Added

- `tools/web/rss_models.py`: `Article` / `FeedWithArticles` / `RssFeeds` pydantic models
  describing the aggregated RSS JSON output contract.
- Dependency: `python-dateutil` (pure-Python) for RSS entry date fallback parsing.
```

- [ ] **Step 7: Run the full suite to verify everything is green**

Run: `cd /Users/fjacquet/Projects/crewai_custom_tools && uv run pytest -q`
Expected: PASS — the entire suite green (all pre-existing tests plus the new SaveToRag and RSS tests). If any test fails, stop and fix before tagging (do not ship a red suite).

- [ ] **Step 8: Commit the release**

```bash
cd /Users/fjacquet/Projects/crewai_custom_tools
git add src/crewai_custom_tools/__init__.py pyproject.toml CHANGELOG.md tests/test_scaffold.py
git commit -m "chore(release): 0.3.0" \
  -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 9: Push `main` (CI runs the test matrix) and confirm it is green**

```bash
cd /Users/fjacquet/Projects/crewai_custom_tools
git push origin main
gh run watch --exit-status || gh run list --branch main --limit 1
```
Expected: the `CI/CD Pipeline` workflow passes on Python 3.11/3.12/3.13. Do not tag until CI is green.

- [ ] **Step 10: Tag and publish the release**

```bash
cd /Users/fjacquet/Projects/crewai_custom_tools
git tag -a v0.3.0 -m "crewai-custom-tools v0.3.0: SaveToRag injection + UnifiedRss pipeline restore"
git push origin v0.3.0
gh release create v0.3.0 --title "v0.3.0" \
  --notes "SaveToRagTool optional rag_tool injection; UnifiedRssTool output-file signature, content-scraping, and invalid-source tracking restored. See CHANGELOG.md."
```
Expected: tag `v0.3.0` exists on the remote and a GitHub release is created. There is **no** publish-on-tag/Docker job — the tag is the consumable artifact. epic_news (Workstream 2) then pins `crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.3.0`.

- [ ] **Step 11: Smoke-verify the tag matches epic_news's expectations** (spec Phase 1 gate)

```bash
cd /Users/fjacquet/Projects/crewai_custom_tools
uv run python -c "
import crewai_custom_tools as c
from crewai_custom_tools import SaveToRagTool, UnifiedRssTool
print('version', c.__version__)
import inspect
print('SaveToRag accepts rag_tool:', 'rag_tool' in inspect.signature(SaveToRagTool.__init__).parameters)
p = list(inspect.signature(UnifiedRssTool._run).parameters)
print('UnifiedRss _run params:', p)
assert p[1:4] == ['opml_file_path', 'days', 'output_file_path']
print('OK')
"
```
Expected: `version 0.3.0`, `SaveToRag accepts rag_tool: True`, `UnifiedRss _run params: ['self', 'opml_file_path', 'days', 'output_file_path', 'invalid_sources_file_path']`, `OK`.

---

## Self-review note

Reviewed against the spec's **Workstream 1** (W1.1/W1.2/W1.3) and the two Tier-C resolutions in the design doc:

- **W1.1 SaveToRagTool injection** — Task 1: `rag_tool: Any = None` field + `__init__(rag_tool=None, **kwargs)` mirroring epic_news's proven pydantic pattern; `_run` uses the injected tool or a lazy default `RagTool()`; `name="save_to_rag"`, `args_schema`, and the `ok()` envelope preserved; the two existing SaveToRag tests kept green; no epic_news import (caller supplies the configured `RagTool`). ✅
- **W1.2 UnifiedRssTool** — Tasks 2 & 3: exact `(opml_file_path, days=7, output_file_path=None, invalid_sources_file_path=None)` signature verified against the positional consumer contract in `rss_utils.py`; `RssFeeds` JSON file-writing with epic_news-identical schema (models replicated in-package, no cross-repo dependency); content-scraping ported as Newspaper3k-optional + in-package `UnifiedScraperTool` (ADR-0002 pure-Python-friendly, reusing the package's own scraper); invalid-source tracking + optional file. Backward-compatible `days`/keyword path retained (no `output_file_path` -> returns an aggregated `ok()` envelope). ✅
- **W1.3 Release** — Task 4: version bumped in both `pyproject.toml` and `__init__.py`, the `tests/test_scaffold.py` version assertion updated via TDD, CHANGELOG entry in the repo's established section style, full suite gate, `main` push + CI-green gate, and `v0.3.0` tag + GitHub release; documented accurately that the tag (not a publish pipeline) is the artifact epic_news pins. ✅
- **Placeholder scan**: every code step contains complete, real code (no TBD/"similar to above"/"add error handling"). **Type consistency**: `Article`/`FeedWithArticles`/`RssFeeds`, `_run`/`_fetch_and_filter_articles`/`_entry_pub_date`/`_scrape_article_content`/`_get_scraper` names and signatures are identical everywhere they appear across Tasks 2–3. **Out of scope** (correctly excluded): BatchArticleScraperTool drop, epic_news migration (Workstream 2), YAGNI-verified unused features.
