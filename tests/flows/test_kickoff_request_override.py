"""kickoff() must honor EPIC_NEWS_REQUEST so the sweep can vary the request
without editing main.py, while falling back to the hardcoded query when unset."""

from unittest.mock import patch

import epic_news.main as main


def test_env_request_seeds_the_flow(monkeypatch):
    monkeypatch.setenv("EPIC_NEWS_REQUEST", "get the rss weekly report")
    with patch.object(main, "ReceptionFlow") as mock_flow:
        mock_flow.return_value.kickoff.return_value = None
        main.kickoff()
    assert mock_flow.call_args.kwargs["user_request"] == "get the rss weekly report"


def test_falls_back_to_hardcoded_query_when_env_unset(monkeypatch):
    monkeypatch.delenv("EPIC_NEWS_REQUEST", raising=False)
    with patch.object(main, "ReceptionFlow") as mock_flow:
        mock_flow.return_value.kickoff.return_value = None
        main.kickoff()
    assert mock_flow.call_args.kwargs["user_request"]  # non-empty default


def test_explicit_arg_wins_over_env(monkeypatch):
    monkeypatch.setenv("EPIC_NEWS_REQUEST", "from env")
    with patch.object(main, "ReceptionFlow") as mock_flow:
        mock_flow.return_value.kickoff.return_value = None
        main.kickoff(user_input="explicit arg")
    assert mock_flow.call_args.kwargs["user_request"] == "explicit arg"
