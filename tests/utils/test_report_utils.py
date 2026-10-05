"""Tests for the report_utils module using pytest."""

import pytest
from faker import Faker

from epic_news.utils.report_utils import (
    _FALLBACK_RECIPIENT,
    prepare_email_params,
)

# Initialize Faker
fake = Faker()


@pytest.fixture
def mock_state():
    """Create a mock state object with realistic test data."""

    class MockState:
        selected_crew = fake.word().title() + "Crew"
        user_request = fake.sentence()
        output_file = f"output/{fake.word()}/report.docx"

    return MockState()


def test_prepare_email_params_defaults(mocker, mock_state):
    """Test prepare_email_params with minimal state."""
    # When sendto is absent, fall back to the known-good recipient (not a crash).
    params = prepare_email_params(mock_state)

    assert params["recipient_email"] == _FALLBACK_RECIPIENT
    assert params["subject"] == f"Epic News Report: {mock_state.selected_crew} - {mock_state.user_request}"
    assert params["body"] == f"Please find the report for '{mock_state.user_request}' attached."
    assert params["attachment_path"] == mock_state.output_file
    assert "output_file" not in params
    assert params["topic"] == f"{mock_state.selected_crew} - {mock_state.user_request}"

    # Test with explicit recipient
    test_email = fake.email()
    mock_state.sendto = test_email
    params = prepare_email_params(mock_state)
    assert params["recipient_email"] == test_email


def test_prepare_email_params_attaches_the_docx_with_the_short_body(mock_state):
    """A DOCX report is attached as is; the body stays the short text."""
    mock_state.output_file = "output/x/report.docx"

    params = prepare_email_params(mock_state)

    assert params["attachment_path"] == "output/x/report.docx"
    assert params["body"] == f"Please find the report for '{mock_state.user_request}' attached."


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
