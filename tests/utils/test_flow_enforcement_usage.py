from types import SimpleNamespace

from loguru import logger

from epic_news.utils import flow_enforcement


def _capture():
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]), level="INFO")
    return messages, sink_id


def _usage(total=10, prompt=7, completion=3, cached=1, requests=2):
    return SimpleNamespace(
        total_tokens=total,
        prompt_tokens=prompt,
        completion_tokens=completion,
        cached_prompt_tokens=cached,
        successful_requests=requests,
    )


def test_log_run_usage_reports_tokens():
    messages, sink_id = _capture()
    try:
        flow_enforcement._log_run_usage("PoemCrew", 1.5, SimpleNamespace(token_usage=_usage()))
    finally:
        logger.remove(sink_id)
    line = next(m for m in messages if m.startswith("📊 Crew PoemCrew"))
    assert "1.50s" in line
    assert "total=10" in line and "prompt=7" in line and "completion=3" in line
    assert "cached=1" in line and "requests=2" in line


def test_log_run_usage_without_usage():
    messages, sink_id = _capture()
    try:
        flow_enforcement._log_run_usage("PoemCrew", 0.25, object())
    finally:
        logger.remove(sink_id)
    assert any(m.startswith("📊 Crew PoemCrew took 0.25s") and "no token usage" in m for m in messages)


class _FakeCrew:
    def kickoff(self, inputs):
        return SimpleNamespace(token_usage=_usage(total=42))


def test_kickoff_flow_logs_usage(monkeypatch):
    monkeypatch.setenv("CREW_KICKOFF_ATTEMPTS", "1")
    messages, sink_id = _capture()
    try:
        flow_enforcement.kickoff_flow(_FakeCrew(), {"topic": "x"})
    finally:
        logger.remove(sink_id)
    assert any(m.startswith("📊 Crew _FakeCrew") and "total=42" in m for m in messages)
