import asyncio
import contextlib
import threading
import time

from epic_news.config import llm_config


def _measure_peak(run_one, workers: int) -> int:
    lock = threading.Lock()
    state = {"now": 0, "peak": 0}

    def body():
        with lock:
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
        time.sleep(0.05)
        with lock:
            state["now"] -= 1
        return "ok"

    threads = [threading.Thread(target=lambda: run_one(body)) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return state["peak"]


def test_sync_calls_never_exceed_cap(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "3")
    llm_config._reset_llm_slots()
    assert _measure_peak(llm_config._with_llm_slot, workers=8) == 3


def test_cap_of_one_serialises(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()
    assert _measure_peak(llm_config._with_llm_slot, workers=4) == 1


def test_invalid_value_falls_back_to_three(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "zero")
    llm_config._reset_llm_slots()
    assert _measure_peak(llm_config._with_llm_slot, workers=6) == 3


def test_async_calls_share_the_cap(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "2")
    llm_config._reset_llm_slots()
    state = {"now": 0, "peak": 0}

    async def body():
        state["now"] += 1
        state["peak"] = max(state["peak"], state["now"])
        await asyncio.sleep(0.05)
        state["now"] -= 1
        return "ok"

    async def main():
        return await asyncio.gather(*(llm_config._awith_llm_slot(body) for _ in range(6)))

    assert asyncio.run(main()) == ["ok"] * 6
    assert state["peak"] == 2


def test_slot_released_on_error(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()

    def boom():
        raise RuntimeError("provider down")

    for _ in range(3):
        with contextlib.suppress(RuntimeError):
            llm_config._with_llm_slot(boom)
    assert llm_config._with_llm_slot(lambda: "still works") == "still works"
