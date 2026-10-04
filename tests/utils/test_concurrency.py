import threading
import time

import pytest

from epic_news.utils.concurrency import bounded_map, concurrency_limit
from epic_news.utils.interrupt import RunCancelledError


def test_results_keep_input_order(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "3")

    def slow_inverse(n):
        time.sleep(0.01 * (5 - n))
        return n * 10

    assert bounded_map(slow_inverse, [1, 2, 3, 4], "TEST_POOL") == [10, 20, 30, 40]


def test_never_more_workers_than_limit(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "2")
    lock = threading.Lock()
    state = {"now": 0, "peak": 0}

    def work(_):
        with lock:
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
        time.sleep(0.03)
        with lock:
            state["now"] -= 1

    bounded_map(work, range(8), "TEST_POOL")
    assert state["peak"] == 2


def test_limit_parsing(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "nope")
    assert concurrency_limit("TEST_POOL") == 3
    monkeypatch.setenv("TEST_POOL", "0")
    assert concurrency_limit("TEST_POOL") == 1
    monkeypatch.delenv("TEST_POOL")
    assert concurrency_limit("TEST_POOL", default=5) == 5


def test_empty_input():
    assert bounded_map(lambda x: x, [], "TEST_POOL") == []


def test_cancellation_stops_pending_work(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "1")
    started: list[int] = []

    def work(n):
        started.append(n)
        if n == 0:
            raise RunCancelledError("user pressed Ctrl+C")
        time.sleep(0.01)
        return n

    with pytest.raises(RunCancelledError):
        bounded_map(work, range(10), "TEST_POOL")
    assert len(started) < 10
