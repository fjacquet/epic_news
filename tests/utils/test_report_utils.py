"""Tests for the report_utils module using pytest."""

import os
import tempfile

from epic_news.utils.report_utils import (
    get_final_report_content,
    prepare_email_params,
    setup_crew_output_directory,
    write_output_to_file,
)


def test_get_final_report_content_found(mocker):
    """Test get_final_report_content when content is found."""
    # Create a mock with strict spec to avoid auto-creation of attributes
    mock_state = mocker.MagicMock(spec=[])
    # Configure only the attributes we need
    mock_state.news_report = "Sample news report content"
    mock_state.recipe = None
    # Configure all other attributes to return None
    mock_attrs = {
        "shopping_advice_report": None,
        "book_summary": None,
        "poem": None,
        "holiday_plan": None,
        "marketing_report": None,
        "meeting_prep_report": None,
        "menu_designer_report": None,
        "contact_info_report": None,
        "cross_reference_report": None,
        "fin_daily_report": None,
        "rss_weekly_report": None,
        "post_report": None,
        "location_report": None,
        "osint_report": None,
        "company_profile": None,
        "tech_stack_report": None,
        "web_presence_report": None,
        "hr_intelligence_report": None,
        "legal_analysis_report": None,
        "geospatial_analysis": None,
        "lead_score_report": None,
        "tech_stack": None,
        "final_report": None,
        "news_daily_report": None,
        "saint_daily_report": None,
    }
    mock_state.configure_mock(**mock_attrs)

    result = get_final_report_content(mock_state)
    assert result == "Sample news report content"


def test_get_final_report_content_not_found(mocker):
    """Test get_final_report_content when no content is found."""
    # Create a mock with strict spec to avoid auto-creation of attributes
    mock_state = mocker.MagicMock(spec=[])
    # Configure all attributes to return None
    mock_attrs = {
        "news_report": None,
        "recipe": None,
        "shopping_advice_report": None,
        "book_summary": None,
        "poem": None,
        "holiday_plan": None,
        "marketing_report": None,
        "meeting_prep_report": None,
        "menu_designer_report": None,
        "contact_info_report": None,
        "cross_reference_report": None,
        "fin_daily_report": None,
        "rss_weekly_report": None,
        "post_report": None,
        "location_report": None,
        "osint_report": None,
        "company_profile": None,
        "tech_stack_report": None,
        "web_presence_report": None,
        "hr_intelligence_report": None,
        "legal_analysis_report": None,
        "geospatial_analysis": None,
        "lead_score_report": None,
        "tech_stack": None,
        "final_report": None,
        "news_daily_report": None,
        "saint_daily_report": None,
    }
    mock_state.configure_mock(**mock_attrs)

    result = get_final_report_content(mock_state)
    assert result is None


def test_write_output_to_file_success():
    """Test write_output_to_file with valid inputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test_output.txt")
        content = "Test content"

        result = write_output_to_file(content, test_file)

        assert result is True
        assert os.path.exists(test_file)
        with open(test_file) as f:
            assert f.read() == content


def test_write_output_to_file_no_content():
    """Test write_output_to_file with no content."""
    test_file = "dummy_path.txt"
    result = write_output_to_file(None, test_file)
    assert result is False


def test_write_output_to_file_no_path():
    """Test write_output_to_file with no file path."""
    content = "Test content"
    result = write_output_to_file(content, None)
    assert result is False


def test_prepare_email_params_defaults(mocker):
    """Test prepare_email_params with minimal state."""
    # Create a mock with strict spec to avoid auto-creation of attributes
    mock_state = mocker.MagicMock(spec=[])
    mock_state.output_file = "test.html"
    # Configure attributes to return None - essential for the default logic
    mock_attrs = {
        "recipient": None,
        "sendto": None,
        "email_subject": None,
        "email_body": None,
        "attachment_file": None,
    }
    mock_state.configure_mock(**mock_attrs)

    # Patch os.environ.get to return None for MAIL
    mocker.patch("os.environ.get", return_value=None)
    params = prepare_email_params(mock_state)

    assert params["recipient_email"] == "sample@example.com"
    assert "subject" in params
    assert "body" in params
    assert "output_file" in params
    assert params["output_file"] == "test.html"


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
