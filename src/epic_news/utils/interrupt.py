"""Make Ctrl+C actually stop a flow run.

CrewAI executes every flow method through ``asyncio.to_thread``. The first Ctrl+C
cancels the asyncio task, but the OS thread running the method is not cancellable: it
keeps calling the provider and writing report files while the interpreter waits to join
it. Observed 2026-08-15 — an interrupted HolidayPlanner run finished 286s after the
interrupt and overwrote ``output/holiday/itinerary.docx`` with placeholder sections,
while the user's replacement run was already in flight against the same paths.

Python cannot cancel that thread, so Ctrl+C does two things at once:

1. **Cooperative cancel.** A global flag is raised, and long loops that would otherwise
   start new provider calls (``kickoff_flow`` retries, per-section narration) check it
   and raise :class:`RunCancelledError` at their next safe point. Nothing new is started and
   no partial report is written.
2. **Watchdog.** A daemon thread force-quits the process after a short grace period, so
   a worker blocked mid-request — where no check can run — cannot outlive the interrupt.
   A second Ctrl+C skips the wait.

The grace period is the only tunable: ``EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS`` (default 5).
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import types
from collections.abc import Callable

from loguru import logger

FORCE_QUIT_EXIT_CODE = 130  # 128 + SIGINT, the shell convention
DEFAULT_GRACE_SECONDS = 5.0

_cancelled = threading.Event()


class RunCancelledError(RuntimeError):
    """Raised at the first safe point after the user interrupted the run."""


def request_cancellation() -> None:
    """Ask every cancellation-aware loop to stop at its next safe point."""
    _cancelled.set()


def reset_cancellation() -> None:
    """Clear the cancellation flag (tests, and any embedder reusing the process)."""
    _cancelled.clear()


def cancellation_requested() -> bool:
    """True once the user has interrupted the run."""
    return _cancelled.is_set()


def raise_if_cancelled(what: str) -> None:
    """Abort before starting `what` if the user has interrupted the run."""
    if _cancelled.is_set():
        raise RunCancelledError(f"Run cancelled by user; refusing to start {what}")


def grace_seconds() -> float:
    """Seconds to let the interpreter unwind before the watchdog force-quits."""
    raw = os.getenv("EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS")
    if not raw:
        return DEFAULT_GRACE_SECONDS
    try:
        return max(0.0, float(raw))
    except ValueError:
        logger.warning("⚠️ Ignoring non-numeric EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS={!r}", raw)
        return DEFAULT_GRACE_SECONDS


def _force_quit() -> None:
    """Leave now, skipping atexit hooks and the non-cancellable thread joins."""
    print("\n🛑 Force quit — abandoning in-flight crew work.", file=sys.stderr, flush=True)
    os._exit(FORCE_QUIT_EXIT_CODE)


def arm_watchdog(delay: float, force_quit: Callable[[], None]) -> threading.Timer:
    """Start a daemon timer that force-quits after `delay` seconds."""
    timer = threading.Timer(delay, force_quit)
    timer.daemon = True  # must never be the thread that keeps the process alive
    timer.start()
    return timer


def make_sigint_handler(
    force_quit: Callable[[], None] = _force_quit,
    arm: Callable[[float, Callable[[], None]], object] = arm_watchdog,
):
    """Build a SIGINT handler: cancel + arm the watchdog, or quit now on a second press."""
    state = {"count": 0}

    def _handler(signum: int, frame: types.FrameType | None) -> None:
        state["count"] += 1
        if state["count"] == 1:
            request_cancellation()
            delay = grace_seconds()
            logger.warning(
                "🛑 Interrupt received — cancelling. Force quit in {:.0f}s "
                "(or press Ctrl+C again to quit now).",
                delay,
            )
            arm(delay, force_quit)
            raise KeyboardInterrupt
        force_quit()

    return _handler


def install_force_quit_handler() -> bool:
    """Install the SIGINT handler. Returns False when the caller is not the main thread.

    Installing our own handler also stops ``asyncio.run`` from installing its own: it
    only does so when the current handler is still ``signal.default_int_handler``. That
    is deliberate — the interrupt count has to live in one place.
    """
    try:
        signal.signal(signal.SIGINT, make_sigint_handler())
    except ValueError:  # not the main thread — signals are unavailable there
        logger.debug("SIGINT force-quit handler not installed (not the main thread)")
        return False
    return True
