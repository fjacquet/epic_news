import asyncio
import contextlib
import threading
import time
from concurrent.futures import Future

import pytest

from epic_news.config import crewai_patches


@pytest.fixture(autouse=True)
def _fresh_slots():
    yield
    crewai_patches._reset_llm_slots()


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
    crewai_patches._reset_llm_slots()
    assert 2 <= _measure_peak(crewai_patches._with_llm_slot, workers=8) <= 3


def test_cap_of_one_serialises(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    crewai_patches._reset_llm_slots()
    assert _measure_peak(crewai_patches._with_llm_slot, workers=4) == 1


def test_invalid_value_falls_back_to_three(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "zero")
    crewai_patches._reset_llm_slots()
    assert 2 <= _measure_peak(crewai_patches._with_llm_slot, workers=6) <= 3


def test_async_calls_share_the_cap(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "2")
    crewai_patches._reset_llm_slots()
    state = {"now": 0, "peak": 0}

    async def body():
        state["now"] += 1
        state["peak"] = max(state["peak"], state["now"])
        await asyncio.sleep(0.05)
        state["now"] -= 1
        return "ok"

    async def main():
        return await asyncio.gather(*(crewai_patches._awith_llm_slot(body) for _ in range(6)))

    assert asyncio.run(main()) == ["ok"] * 6
    assert 1 <= state["peak"] <= 2


def test_slot_released_on_error(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    crewai_patches._reset_llm_slots()

    def boom():
        raise RuntimeError("provider down")

    for _ in range(3):
        with contextlib.suppress(RuntimeError):
            crewai_patches._with_llm_slot(boom)
    assert crewai_patches._with_llm_slot(lambda: "still works") == "still works"


def test_nested_sync_slot_is_reentrant(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    crewai_patches._reset_llm_slots()
    result = []
    t = threading.Thread(
        target=lambda: result.append(
            crewai_patches._with_llm_slot(lambda: crewai_patches._with_llm_slot(lambda: "in"))
        )
    )
    t.start()
    t.join(timeout=3)
    assert result == ["in"]


def test_nested_async_slot_is_reentrant(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    crewai_patches._reset_llm_slots()

    async def inner():
        return "in"

    async def outer():
        return await crewai_patches._awith_llm_slot(inner)

    async def main():
        return await asyncio.wait_for(crewai_patches._awith_llm_slot(outer), timeout=3)

    assert asyncio.run(main()) == "in"


def test_cancelled_async_waiter_does_not_leak_slot(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    crewai_patches._reset_llm_slots()

    async def body():
        return "x"

    async def main():
        slots = crewai_patches._slots()
        slots.acquire()  # holder
        waiter = asyncio.create_task(crewai_patches._awith_llm_slot(body))
        await asyncio.sleep(0.1)
        waiter.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await waiter
        slots.release()
        await asyncio.sleep(0.1)

    asyncio.run(main())
    slots = crewai_patches._slots()
    assert slots.acquire(blocking=False)
    slots.release()
    assert crewai_patches._with_llm_slot(lambda: "ok") == "ok"


def test_patched_call_path_goes_through_slot(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("LLM_EMPTY_RETRIES", "0")
    crewai_patches._reset_llm_slots()
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

    crewai_patches._wrap_call_for_react_safety(Stub)
    stub = Stub()
    threads = [threading.Thread(target=stub.call) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert state["peak"] == 1


def _run_on_loop_with_timeout(coro_factory, timeout: float = 5.0):
    """Run ``asyncio.run(coro_factory())`` in a daemon thread; never hang the suite."""
    result: list = []
    t = threading.Thread(target=lambda: result.append(asyncio.run(coro_factory())), daemon=True)
    t.start()
    t.join(timeout=timeout)
    return t.is_alive(), result


def test_sync_call_on_loop_thread_does_not_deadlock_when_slots_held_by_coroutines(monkeypatch):
    # Regression (final review I1): coroutines on one loop hold every slot while a
    # sync call on that same loop thread (crewai's sync summarize_messages inside an
    # async executor) waits for a slot. Blocking the loop would hang forever.
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "3")
    crewai_patches._reset_llm_slots()

    async def holder():
        return await crewai_patches._awith_llm_slot(lambda: asyncio.sleep(0.5))

    async def summariser():
        await asyncio.sleep(0.1)  # all 3 slots now held by the holders
        return crewai_patches._with_llm_slot(lambda: "summary")

    async def main():
        return await asyncio.gather(*(holder() for _ in range(3)), summariser())

    still_blocked, result = _run_on_loop_with_timeout(main)
    assert not still_blocked, "sync LLM call on an event-loop thread deadlocked"
    assert result[0][-1] == "summary"


def test_sync_call_on_loop_thread_takes_a_free_slot(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    crewai_patches._reset_llm_slots()
    seen: dict = {}

    def body():
        slots = crewai_patches._slots()
        seen["slot_free_during_call"] = slots.acquire(blocking=False)
        if seen["slot_free_during_call"]:
            slots.release()
        return "ok"

    async def main():
        return crewai_patches._with_llm_slot(body)

    still_blocked, result = _run_on_loop_with_timeout(main)
    assert not still_blocked
    assert result == ["ok"]
    assert seen["slot_free_during_call"] is False  # the call held the only slot
    slots = crewai_patches._slots()
    assert slots.acquire(blocking=False)  # and released it afterwards
    slots.release()


def _assert_all_slots_free(limit: int) -> None:
    slots = crewai_patches._slots()
    taken = [slots.acquire(blocking=False) for _ in range(limit + 1)]
    for ok in taken:
        if ok:
            slots.release()
    assert taken == [True] * limit + [False]


def test_sync_waiter_gives_up_after_slot_wait_and_runs_uncapped(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("LLM_SLOT_WAIT_SECONDS", "0.2")
    crewai_patches._reset_llm_slots()
    slots = crewai_patches._slots()
    slots.acquire()  # held elsewhere for the whole call
    result: list = []
    t = threading.Thread(
        target=lambda: result.append(crewai_patches._with_llm_slot(lambda: "ran")), daemon=True
    )
    t.start()
    t.join(timeout=5)
    slots.release()
    assert not t.is_alive()
    assert result == ["ran"]
    _assert_all_slots_free(1)  # the uncapped call released nothing it did not take


def test_uncapped_call_is_reentrant_and_nested_call_does_not_wait(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("LLM_SLOT_WAIT_SECONDS", "0.5")
    crewai_patches._reset_llm_slots()
    slots = crewai_patches._slots()
    slots.acquire()
    seen: dict = {}

    def outer():
        seen["holds"] = crewai_patches._holds_slot.get()
        start = time.monotonic()
        seen["nested"] = crewai_patches._with_llm_slot(lambda: "in")
        seen["nested_seconds"] = time.monotonic() - start
        return "out"

    result: list = []
    t = threading.Thread(target=lambda: result.append(crewai_patches._with_llm_slot(outer)), daemon=True)
    t.start()
    t.join(timeout=5)
    slots.release()
    assert result == ["out"]
    assert seen["holds"] is True
    assert seen["nested"] == "in"
    assert seen["nested_seconds"] < 0.25  # did not wait another 0.5 s
    _assert_all_slots_free(1)


def test_async_waiter_gives_up_after_slot_wait_and_runs_uncapped(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("LLM_SLOT_WAIT_SECONDS", "0.2")
    crewai_patches._reset_llm_slots()
    slots = crewai_patches._slots()
    slots.acquire()

    async def body():
        return "ran"

    async def main():
        return await asyncio.wait_for(crewai_patches._awith_llm_slot(body), timeout=5)

    still_blocked, result = _run_on_loop_with_timeout(main)
    slots.release()
    assert not still_blocked
    assert result == ["ran"]
    _assert_all_slots_free(1)


def test_multi_chunk_summary_on_helper_loop_does_not_deadlock(monkeypatch):
    # Regression (final review I1, multi-chunk variant): coroutines on loop A hold every
    # slot; the loop-A thread blocks on a pool future whose worker runs
    # asyncio.run(_awith_llm_slot(...)) (crewai summarize_messages with several chunks).
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "3")
    monkeypatch.setenv("LLM_SLOT_WAIT_SECONDS", "0.3")
    crewai_patches._reset_llm_slots()

    async def holder():
        return await crewai_patches._awith_llm_slot(lambda: asyncio.sleep(0.5))

    async def chunk():
        return "summary"

    async def summariser():
        await asyncio.sleep(0.1)  # all 3 slots now held by the holders
        # A daemon helper (not a ThreadPoolExecutor, whose workers are joined at exit)
        # so a deadlock fails the test instead of hanging the interpreter.
        future: Future = Future()
        coro = crewai_patches._awith_llm_slot(chunk)
        threading.Thread(target=lambda: future.set_result(asyncio.run(coro)), daemon=True).start()
        return future.result()  # blocks the loop-A thread, like crewai's pool.submit(...).result()

    async def main():
        return await asyncio.gather(*(holder() for _ in range(3)), summariser())

    still_blocked, result = _run_on_loop_with_timeout(main)
    assert not still_blocked, "multi-chunk summary on a helper loop deadlocked"
    assert result[0][-1] == "summary"
    _assert_all_slots_free(3)
