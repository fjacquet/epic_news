"""Run named benchmark requests through ReceptionFlow and print per-crew cost.

Usage: uv run python scripts/bench_flow.py pestel news_daily

LIVE: every request is a full flow run against the configured LLM provider.
"""

import json
import os
import re
import sys
import threading
import time
from pathlib import Path

import litellm
from litellm.integrations.custom_logger import CustomLogger
from loguru import logger

import epic_news.main as main_mod

_REQUESTS = Path(__file__).with_name("bench_requests.json")
_LINE = re.compile(
    r"^📊 Crew (?P<crew>\S+) took (?P<seconds>[\d.]+)s"
    r"(?: — tokens: total=(?P<total>\d+) prompt=(?P<prompt>\d+) completion=(?P<completion>\d+)"
    r" cached=\d+ requests=(?P<requests>\d+))?"
)


def parse_usage_line(line: str) -> dict | None:
    match = _LINE.match(line)
    if not match:
        return None

    def _int(key: str) -> int | None:
        value = match.group(key)
        return int(value) if value is not None else None

    return {
        "crew": match.group("crew"),
        "seconds": float(match.group("seconds")),
        "total": _int("total"),
        "prompt": _int("prompt"),
        "completion": _int("completion"),
        "requests": _int("requests"),
    }


class UsageCounter(CustomLogger):
    """Sum every successful LiteLLM call, including structured-output ones CrewAI misses."""

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self.calls = 0
        self.prompt = 0
        self.completion = 0
        self.total = 0

    def _record(self, response_obj) -> None:
        usage = response_obj.get("usage") if hasattr(response_obj, "get") else None
        if usage is None:
            usage = getattr(response_obj, "usage", None)

        def _field(key: str) -> int:
            value = usage.get(key) if isinstance(usage, dict) else getattr(usage, key, None)
            return int(value or 0)

        with self._lock:
            self.calls += 1
            self.prompt += _field("prompt_tokens")
            self.completion += _field("completion_tokens")
            self.total += _field("total_tokens")

    def log_success_event(self, kwargs, response_obj, start_time, end_time) -> None:
        self._record(response_obj)

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time) -> None:
        self._record(response_obj)

    def as_dict(self) -> dict:
        return {
            "calls": self.calls,
            "prompt": self.prompt,
            "completion": self.completion,
            "total": self.total,
        }


def register_counter(counter: UsageCounter) -> None:
    """CrewAI resets litellm.callbacks per LLM; sync calls read success_callback, async ones the private list."""
    litellm.success_callback.append(counter)
    litellm._async_success_callback.append(counter)


def unregister_counter(counter: UsageCounter) -> None:
    for registry in (litellm.success_callback, litellm._async_success_callback):
        if counter in registry:
            registry.remove(counter)


def run(name: str, request: str) -> dict:
    crews: list[dict] = []

    def sink(message) -> None:
        parsed = parse_usage_line(message.record["message"])
        if parsed:
            crews.append(parsed)

    # kickoff() calls setup_logging(), which removes every loguru handler; attach the
    # capture sink right after it instead of before the run.
    original_setup = main_mod.setup_logging
    sink_ids: list[int] = []

    def setup_logging_then_capture(*args, **kwargs):
        original_setup(*args, **kwargs)
        sink_ids.append(logger.add(sink, level="INFO"))

    main_mod.setup_logging = setup_logging_then_capture
    counter = UsageCounter()
    register_counter(counter)
    start = time.perf_counter()
    try:
        main_mod.kickoff(user_input=request)
    finally:
        unregister_counter(counter)
        main_mod.setup_logging = original_setup
        for sink_id in sink_ids:
            logger.remove(sink_id)
    return {
        "name": name,
        "elapsed_s": round(time.perf_counter() - start, 1),
        "crews": crews,
        "litellm": counter.as_dict(),
    }


def main(names: list[str]) -> None:
    os.environ["EPIC_ENABLE_EMAIL"] = "false"  # bench runs must never email the report
    requests = json.loads(_REQUESTS.read_text(encoding="utf-8"))
    for name in names:
        print(json.dumps(run(name, requests[name]), ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
