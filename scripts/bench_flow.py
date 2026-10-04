"""Run named benchmark requests through ReceptionFlow and print per-crew cost.

Usage: uv run python scripts/bench_flow.py pestel news_daily

LIVE: every request is a full flow run against the configured LLM provider.
"""

import json
import re
import sys
import time
from pathlib import Path

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
    start = time.perf_counter()
    try:
        main_mod.kickoff(user_input=request)
    finally:
        main_mod.setup_logging = original_setup
        for sink_id in sink_ids:
            logger.remove(sink_id)
    return {"name": name, "elapsed_s": round(time.perf_counter() - start, 1), "crews": crews}


def main(names: list[str]) -> None:
    requests = json.loads(_REQUESTS.read_text(encoding="utf-8"))
    for name in names:
        print(json.dumps(run(name, requests[name]), ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
