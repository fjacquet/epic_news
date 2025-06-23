from unittest.mock import patch

from fastapi.testclient import TestClient

from epic_news.api import app

client = TestClient(app)


@patch("epic_news.api.kickoff")
def test_kickoff_endpoint_success(mock_kickoff):
    """Test the /kickoff endpoint for a successful request."""
    # Arrange
    user_request = "Find the latest news on AI."

    # Act
    response = client.post("/kickoff", json={"user_request": user_request})

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
    response = client.post("/kickoff", json={"wrong_field": "test"})

    # Assert
    assert response.status_code == 422  # Unprocessable Entity
