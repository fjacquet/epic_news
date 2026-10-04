"""Bounded, order-preserving parallel map for blocking work (LLM calls, crew runs)."""

import os
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor


def concurrency_limit(env_var: str, default: int = 3) -> int:
    """Worker count from env_var (minimum 1; invalid values fall back to default)."""
    try:
        return max(1, int(os.getenv(env_var, str(default))))
    except ValueError:
        return default


def bounded_map[T, R](func: Callable[[T], R], items: Iterable[T], env_var: str, default: int = 3) -> list[R]:
    """Apply func to every item with at most concurrency_limit(env_var) threads.

    Results follow input order. The first exception (including RunCancelledError)
    cancels work that has not started yet and is re-raised.
    """
    batch = list(items)
    if not batch:
        return []
    workers = min(concurrency_limit(env_var, default), len(batch))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(func, item) for item in batch]
        try:
            return [future.result() for future in futures]
        except BaseException:
            for future in futures:
                future.cancel()
            raise
