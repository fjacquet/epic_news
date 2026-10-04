import threading
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from epic_news import api
from epic_news.api import app

client = TestClient(app)

TOKEN = "test-token-0123456789abcdef"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def _api_env(monkeypatch):
    monkeypatch.setenv("EPIC_API_TOKEN", TOKEN)
    monkeypatch.setattr(api, "_kickoff_slots", threading.BoundedSemaphore(1))


@patch("epic_news.api.kickoff")
def test_kickoff_endpoint_success(mock_kickoff):
    """Test the /kickoff endpoint for a successful request."""
    # Arrange
    user_request = "Find the latest news on AI."

    # Act
    response = client.post("/kickoff", json={"user_request": user_request}, headers=AUTH)

    # Assert
    assert response.status_code == 202
    assert response.json() == {
        "message": "Crew kickoff initiated successfully.",
        "user_request": user_request,
    }
    mock_kickoff.assert_called_once_with(user_input=user_request)


def test_kickoff_endpoint_validation_error():
    """Test the /kickoff endpoint with a missing user_request."""
    # Act
    response = client.post("/kickoff", json={"wrong_field": "test"}, headers=AUTH)

    # Assert
    assert response.status_code == 422  # Unprocessable Entity


@patch("epic_news.api.kickoff")
def test_kickoff_rejects_overlong_request(mock_kickoff):
    response = client.post("/kickoff", json={"user_request": "x" * 2001}, headers=AUTH)

    assert response.status_code == 422
    mock_kickoff.assert_not_called()


@patch("epic_news.api.kickoff")
def test_kickoff_missing_token_is_401(mock_kickoff):
    response = client.post("/kickoff", json={"user_request": "hi"})

    assert response.status_code == 401
    mock_kickoff.assert_not_called()


@patch("epic_news.api.kickoff")
def test_kickoff_wrong_token_is_401(mock_kickoff):
    response = client.post("/kickoff", json={"user_request": "hi"}, headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401
    assert TOKEN not in response.text
    mock_kickoff.assert_not_called()


@pytest.mark.parametrize("value", [None, ""])
@patch("epic_news.api.kickoff")
def test_kickoff_fails_closed_without_configured_token(mock_kickoff, monkeypatch, value):
    if value is None:
        monkeypatch.delenv("EPIC_API_TOKEN", raising=False)
    else:
        monkeypatch.setenv("EPIC_API_TOKEN", value)

    response = client.post("/kickoff", json={"user_request": "hi"}, headers={"Authorization": "Bearer "})

    assert response.status_code == 503
    mock_kickoff.assert_not_called()


@patch("epic_news.api.kickoff")
def test_kickoff_returns_429_when_all_slots_busy(mock_kickoff):
    assert api._kickoff_slots.acquire(blocking=False)  # simulate a running kickoff

    response = client.post("/kickoff", json={"user_request": "hi"}, headers=AUTH)

    assert response.status_code == 429
    mock_kickoff.assert_not_called()


@patch("epic_news.api.kickoff")
def test_kickoff_slot_released_after_background_run(mock_kickoff):
    first = client.post("/kickoff", json={"user_request": "one"}, headers=AUTH)
    second = client.post("/kickoff", json={"user_request": "two"}, headers=AUTH)

    assert first.status_code == 202
    assert second.status_code == 202
    assert mock_kickoff.call_count == 2


@patch("epic_news.api.kickoff", side_effect=RuntimeError("boom"))
def test_kickoff_slot_released_when_background_run_fails(mock_kickoff):
    failing_client = TestClient(app, raise_server_exceptions=False)
    failing_client.post("/kickoff", json={"user_request": "one"}, headers=AUTH)

    assert api._kickoff_slots.acquire(blocking=False)


def test_health_endpoint():
    """The container HEALTHCHECK and docker-compose both probe this route."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
