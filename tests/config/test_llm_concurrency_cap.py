import asyncio
import contextlib
import threading
import time

import pytest

from epic_news.config import llm_config


@pytest.fixture(autouse=True)
def _fresh_slots():
    yield
    llm_config._reset_llm_slots()


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
    assert 2 <= _measure_peak(llm_config._with_llm_slot, workers=8) <= 3


def test_cap_of_one_serialises(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()
    assert _measure_peak(llm_config._with_llm_slot, workers=4) == 1


def test_invalid_value_falls_back_to_three(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "zero")
    llm_config._reset_llm_slots()
    assert 2 <= _measure_peak(llm_config._with_llm_slot, workers=6) <= 3


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
    assert 1 <= state["peak"] <= 2


def test_slot_released_on_error(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()

    def boom():
        raise RuntimeError("provider down")

    for _ in range(3):
        with contextlib.suppress(RuntimeError):
            llm_config._with_llm_slot(boom)
    assert llm_config._with_llm_slot(lambda: "still works") == "still works"


def test_nested_sync_slot_is_reentrant(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()
    result = []
    t = threading.Thread(
        target=lambda: result.append(
            llm_config._with_llm_slot(lambda: llm_config._with_llm_slot(lambda: "in"))
        )
    )
    t.start()
    t.join(timeout=3)
    assert result == ["in"]


def test_nested_async_slot_is_reentrant(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()

    async def inner():
        return "in"

    async def outer():
        return await llm_config._awith_llm_slot(inner)

    async def main():
        return await asyncio.wait_for(llm_config._awith_llm_slot(outer), timeout=3)

    assert asyncio.run(main()) == "in"


def test_cancelled_async_waiter_does_not_leak_slot(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()

    async def body():
        return "x"

    async def main():
        slots = llm_config._slots()
        slots.acquire()  # holder
        waiter = asyncio.create_task(llm_config._awith_llm_slot(body))
        await asyncio.sleep(0.1)
        waiter.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await waiter
        slots.release()
        await asyncio.sleep(0.1)

    asyncio.run(main())
    slots = llm_config._slots()
    assert slots.acquire(blocking=False)
    slots.release()
    assert llm_config._with_llm_slot(lambda: "ok") == "ok"


def test_patched_call_path_goes_through_slot(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("LLM_EMPTY_RETRIES", "0")
    llm_config._reset_llm_slots()
    lock = threading.Lock()
    state = {"now": 0, "peak": 0}

    class Stub:
        model = "stub"

        def call(self, *args, **kwargs):
            with lock:
                state["now"] += 1
                state["peak"] = max(state["peak"], state["now"])
            time.sleep(0.05)
            with lock:
                state["now"] -= 1
            return "text"

    llm_config._wrap_call_for_react_safety(Stub)
    stub = Stub()
    threads = [threading.Thread(target=stub.call) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert state["peak"] == 1
