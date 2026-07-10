"""Tests for the report_utils module using pytest."""

import os

import pytest
from faker import Faker

from epic_news.utils.report_utils import (
    _FALLBACK_RECIPIENT,
    prepare_email_params,
    setup_crew_output_directory,
)

# Initialize Faker
fake = Faker()


@pytest.fixture
def mock_state():
    """Create a mock state object with realistic test data."""

    class MockState:
        selected_crew = fake.word().title() + "Crew"
        user_request = fake.sentence()
        output_file = f"{fake.word()}.html"

    return MockState()


def test_prepare_email_params_defaults(mocker, mock_state):
    """Test prepare_email_params with minimal state."""
    # When sendto is absent, fall back to the known-good recipient (not a crash).
    params = prepare_email_params(mock_state)

    assert params["recipient_email"] == _FALLBACK_RECIPIENT
    assert params["subject"] == f"Epic News Report: {mock_state.selected_crew} - {mock_state.user_request}"
    assert params["body"] == f"Please find the report for '{mock_state.user_request}' attached."
    # output_file names a file that was never rendered, so there is nothing to attach.
    # Handing back a dangling path is what made Composio treat it as an uploaded S3 key.
    assert params["attachment_path"] is None
    assert params["output_file"] == mock_state.output_file
    assert params["topic"] == f"{mock_state.selected_crew} - {mock_state.user_request}"

    # Test with explicit recipient
    test_email = fake.email()
    mock_state.sendto = test_email
    params = prepare_email_params(mock_state)
    assert params["recipient_email"] == test_email


def test_prepare_email_params_attaches_a_report_that_exists(mock_state, tmp_path):
    """When the crew actually rendered the report, it is both body and attachment."""
    report = tmp_path / "report.html"
    report.write_text("<html></html>", encoding="utf-8")
    mock_state.output_file = str(report)

    params = prepare_email_params(mock_state)

    assert params["attachment_path"] == str(report)
    assert params["output_file"] == str(report)


@pytest.mark.parametrize(
    "bad_sendto",
    ["", "   ", "not-an-email", "@no-local.com", "no-at-sign", "missing@tld", "a b@c.com"],
)
def test_prepare_email_params_invalid_recipient_falls_back(mock_state, bad_sendto):
    """A missing/empty/malformed MAIL must fall back, not reach the email tool."""
    mock_state.sendto = bad_sendto
    params = prepare_email_params(mock_state)
    assert params["recipient_email"] == _FALLBACK_RECIPIENT


def test_prepare_email_params_trims_valid_recipient(mock_state):
    """A valid but whitespace-padded address is accepted and trimmed."""
    mock_state.sendto = "  user@example.com  "
    params = prepare_email_params(mock_state)
    assert params["recipient_email"] == "user@example.com"


def test_setup_crew_output_directory_exists(mocker):
    """Test setup_crew_output_directory when directory already exists."""
    # Setup
    crew_name = fake.word()
    # setup_crew_output_directory lowercases the crew name, so the expected
    # path must too. fake.word() is unseeded and occasionally returns a
    # capitalized token (e.g. "American"), which made this assertion flaky.
    expected_path = os.path.join("output", crew_name.lower())

    # Mock dependencies
    mock_ensure_output_directory = mocker.patch("epic_news.utils.report_utils.ensure_output_directory")
    mocker.patch("os.path.exists", return_value=True)

    # Execute
    result = setup_crew_output_directory(crew_name)

    # Assert
    assert result == expected_path
    mock_ensure_output_directory.assert_called_once_with(expected_path)


def test_setup_crew_output_directory_create(mocker):
    """Test setup_crew_output_directory when directory needs to be created."""
    # Setup
    crew_name = fake.word()
    expected_path = os.path.join("output", crew_name.lower())

    # Mock dependencies
    mock_ensure_output_directory = mocker.patch("epic_news.utils.report_utils.ensure_output_directory")
    mocker.patch("os.path.exists", return_value=False)

    # Execute
    result = setup_crew_output_directory(crew_name)

    # Assert
    assert result == expected_path
    mock_ensure_output_directory.assert_called_once_with(expected_path)
