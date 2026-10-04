"""Measure routing accuracy: extraction + classification on a fixed request set.

Usage: EPIC_ENABLE_EMAIL=false env -u VIRTUAL_ENV uv run python scripts/eval_routing.py
LIVE: runs the extraction and classification crews per request (no other crew).
"""

import importlib.util
import json
import time
from pathlib import Path

import litellm

from epic_news.main import ReceptionFlow
from epic_news.utils.directory_utils import ensure_output_directories

_DATA = Path(__file__).with_name("routing_eval_requests.json")
_BENCH = Path(__file__).with_name("bench_flow.py")

_bench_spec = importlib.util.spec_from_file_location("bench_flow", _BENCH)
bench_flow = importlib.util.module_from_spec(_bench_spec)
_bench_spec.loader.exec_module(bench_flow)


def score(results: list[tuple[str, str]]) -> tuple[int, int]:
    return sum(expected == actual for expected, actual in results), len(results)


def route(request: str) -> str:
    flow = ReceptionFlow(user_request=request)
    flow.state.user_request = request
    flow.extract_info()
    flow.classify()
    return flow.state.selected_crew


def main() -> None:
    ensure_output_directories()
    rows = json.loads(_DATA.read_text(encoding="utf-8"))
    counter = bench_flow.UsageCounter()
    # CrewAI resets litellm.callbacks on every LLM it builds, so register in success_callback.
    litellm.success_callback.append(counter)
    start = time.perf_counter()
    results = []
    try:
        for row in rows:
            actual = route(row["request"])
            results.append((row["expected"], actual))
            mark = "OK " if actual == row["expected"] else "BAD"
            print(f"{mark} expected={row['expected']:<26} actual={actual:<26} {row['request']}")
    finally:
        if counter in litellm.success_callback:
            litellm.success_callback.remove(counter)
    correct, total = score(results)
    print(f"accuracy={correct}/{total}")
    print(
        f"litellm calls={counter.calls} prompt={counter.prompt} "
        f"completion={counter.completion} total={counter.total}"
    )
    print(f"wall={time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
