import asyncio
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("bench_flow", Path("scripts/bench_flow.py"))
bench_flow = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench_flow)


def test_parse_usage_line():
    line = "📊 Crew PestelCrew took 312.40s — tokens: total=120000 prompt=100000 completion=20000 cached=0 requests=45"
    assert bench_flow.parse_usage_line(line) == {
        "crew": "PestelCrew",
        "seconds": 312.4,
        "total": 120000,
        "prompt": 100000,
        "completion": 20000,
        "requests": 45,
    }


def test_parse_usage_line_ignores_other_lines():
    assert bench_flow.parse_usage_line("🚀 Kicking off crew PestelCrew") is None
    assert bench_flow.parse_usage_line("📊 Crew PoemCrew took 1.00s (no token usage reported)") == {
        "crew": "PoemCrew",
        "seconds": 1.0,
        "total": None,
        "prompt": None,
        "completion": None,
        "requests": None,
    }


def test_usage_counter_sums_sync_and_async_events():
    counter = bench_flow.UsageCounter()
    sync_resp = {"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}

    class Usage:
        prompt_tokens = 7
        completion_tokens = 3
        total_tokens = 10

    class Resp:
        usage = Usage()

        def get(self, key, default=None):
            return getattr(self, key, default)

    counter.log_success_event({}, sync_resp, None, None)
    asyncio.run(counter.async_log_success_event({}, Resp(), None, None))
    assert counter.as_dict() == {"calls": 2, "prompt": 17, "completion": 8, "total": 25}
