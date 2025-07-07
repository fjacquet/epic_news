"""Tests for the report_utils module using pytest."""

from epic_news.utils.report_utils import (
    prepare_email_params,
    setup_crew_output_directory,
)


def test_prepare_email_params_defaults(mocker):
    """Test prepare_email_params with minimal state."""
    # Create a mock with necessary attributes
    mock_state = mocker.MagicMock()
    mock_state.selected_crew = "TestCrew"
    mock_state.user_request = "Test Request"
    mock_state.output_file = "test.html"

    params = prepare_email_params(mock_state)

    assert params["recipient"] == "test-ia@fjaquet.fr"
    assert params["subject"] == "Epic News Report: TestCrew - Test Request"
    assert params["body"] == "Please find the report for 'Test Request' attached."
    assert params["attachment_path"] == "test.html"


"""Tests for the report_utils module using pytest."""


def test_setup_crew_output_directory_exists(mocker):
    """Test setup_crew_output_directory when directory already exists."""
    mock_ensure_output_directory = mocker.patch("epic_news.utils.report_utils.ensure_output_directory")
    mocker.patch("os.path.exists", return_value=True)
    result = setup_crew_output_directory("test_crew")

    assert result == "output/test_crew"
    mock_ensure_output_directory.assert_called_once_with("output/test_crew")


def test_setup_crew_output_directory_create(mocker):
    """Test setup_crew_output_directory when directory needs to be created."""
    mock_ensure_output_directory = mocker.patch("epic_news.utils.report_utils.ensure_output_directory")
    mocker.patch("os.path.exists", return_value=False)
    result = setup_crew_output_directory("test_crew")

    assert result == "output/test_crew"
    mock_ensure_output_directory.assert_called_once_with("output/test_crew")
