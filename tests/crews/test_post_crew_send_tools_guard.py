"""PostCrew must not report an email as delivered when it cannot send.

Observed in a real run: Composio returned HTTP 401 (invalid API key), _get_send_tools()
swallowed it and returned [], and the resulting tool-less agent filled in
PostResult(status="success"). The flow logged a delivered email that never existed.

The guard lives on the send path (`can_send`), not on the construction path, so the crew
can still be built and unit-tested in CI where Composio credentials are absent.
"""

from epic_news.crews.post.post_crew import PostCrew


def test_can_send_is_false_without_send_tools(monkeypatch):
    monkeypatch.setattr(PostCrew, "_get_send_tools", lambda self: [])
    assert PostCrew().can_send() is False


def test_can_send_is_true_with_send_tools(monkeypatch):
    monkeypatch.setattr(PostCrew, "_get_send_tools", lambda self: [object()])
    assert PostCrew().can_send() is True


def test_crew_still_builds_without_credentials(monkeypatch):
    """Construction must not require Composio; only sending does."""
    monkeypatch.setattr(PostCrew, "_get_send_tools", lambda self: [])
    crew = PostCrew().crew()
    assert crew.tasks, "PostCrew should still build its tasks without send tools"
