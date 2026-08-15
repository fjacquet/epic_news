"""Ctrl+C escape hatch: cancel + watchdog on the first press, quit now on the second."""

import signal
import threading

import pytest

from epic_news.utils.interrupt import (
    DEFAULT_GRACE_SECONDS,
    FORCE_QUIT_EXIT_CODE,
    RunCancelledError,
    arm_watchdog,
    cancellation_requested,
    grace_seconds,
    install_force_quit_handler,
    make_sigint_handler,
    raise_if_cancelled,
    request_cancellation,
    reset_cancellation,
)


@pytest.fixture(autouse=True)
def _clean_cancellation_flag():
    reset_cancellation()
    yield
    reset_cancellation()


def _handler(quits: list, armed: list):
    return make_sigint_handler(
        force_quit=lambda: quits.append(True),
        arm=lambda delay, fn: armed.append((delay, fn)),
    )


def test_first_interrupt_cancels_arms_watchdog_and_unwinds():
    quits: list = []
    armed: list = []
    handler = _handler(quits, armed)

    with pytest.raises(KeyboardInterrupt):
        handler(signal.SIGINT, None)

    assert cancellation_requested() is True
    assert quits == []  # grace period, not an immediate kill
    assert len(armed) == 1
    assert armed[0][0] == DEFAULT_GRACE_SECONDS


def test_armed_watchdog_force_quits_when_it_fires():
    """The armed callback is the real force-quit, not a no-op."""
    quits: list = []
    armed: list = []
    handler = _handler(quits, armed)

    with pytest.raises(KeyboardInterrupt):
        handler(signal.SIGINT, None)
    armed[0][1]()  # simulate the grace period elapsing

    assert quits == [True]


def test_second_interrupt_quits_without_waiting():
    quits: list = []
    armed: list = []
    handler = _handler(quits, armed)

    with pytest.raises(KeyboardInterrupt):
        handler(signal.SIGINT, None)
    handler(signal.SIGINT, None)

    assert quits == [True]
    assert len(armed) == 1  # not re-armed


def test_handlers_do_not_share_interrupt_count():
    first = _handler([], [])
    second = _handler([], [])

    with pytest.raises(KeyboardInterrupt):
        first(signal.SIGINT, None)
    with pytest.raises(KeyboardInterrupt):
        second(signal.SIGINT, None)


def test_raise_if_cancelled_is_quiet_until_cancelled():
    raise_if_cancelled("something")  # no-op

    request_cancellation()

    with pytest.raises(RunCancelledError, match="something"):
        raise_if_cancelled("something")


def test_watchdog_thread_never_keeps_the_process_alive():
    fired = threading.Event()
    timer = arm_watchdog(0.01, fired.set)

    assert timer.daemon is True
    assert fired.wait(2) is True


def test_grace_seconds_reads_the_environment(monkeypatch):
    monkeypatch.setenv("EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS", "0.5")
    assert grace_seconds() == 0.5

    monkeypatch.setenv("EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS", "-3")
    assert grace_seconds() == 0.0  # negative means "quit now", not "wait forever"

    monkeypatch.setenv("EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS", "soon")
    assert grace_seconds() == DEFAULT_GRACE_SECONDS

    monkeypatch.delenv("EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS")
    assert grace_seconds() == DEFAULT_GRACE_SECONDS


def test_install_registers_handler():
    previous = signal.getsignal(signal.SIGINT)
    try:
        assert install_force_quit_handler() is True
        # Own handler installed, so asyncio.run leaves SIGINT alone (it only takes over
        # when the current handler is still signal.default_int_handler).
        assert signal.getsignal(signal.SIGINT) is not signal.default_int_handler
    finally:
        signal.signal(signal.SIGINT, previous)


def test_install_is_a_noop_off_the_main_thread():
    result: list[bool] = []
    worker = threading.Thread(target=lambda: result.append(install_force_quit_handler()))
    worker.start()
    worker.join()

    assert result == [False]


def test_force_quit_uses_the_shell_sigint_convention():
    assert FORCE_QUIT_EXIT_CODE == 130
