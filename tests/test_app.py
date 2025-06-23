from queue import Queue
from unittest.mock import MagicMock, mock_open, patch

from epic_news.app import run_crew_thread


@patch("epic_news.app.kickoff")
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="<html>Report</html>")
def test_run_crew_thread_success(mock_file, mock_exists, mock_kickoff):
    """Test the crew thread function for a successful run with an output file."""
    # Arrange
    log_queue = Queue()
    user_request = "Test request"
    mock_flow = MagicMock()
    mock_flow.state.output_file = "/path/to/report.html"
    mock_kickoff.return_value = mock_flow

    # Act
    run_crew_thread(user_request, log_queue)

    # Assert
    results = list(log_queue.queue)
    assert any(item[0] == "REPORT" and item[1] == "<html>Report</html>" for item in results)
    assert any(item[0] == "END" for item in results)
    mock_kickoff.assert_called_once_with(user_input=user_request)


@patch("epic_news.app.kickoff")
@patch("os.path.exists", return_value=False)
def test_run_crew_thread_no_output_file(mock_exists, mock_kickoff):
    """Test the crew thread function when the output file is not found."""
    # Arrange
    log_queue = Queue()
    user_request = "Test request"
    mock_flow = MagicMock()
    mock_flow.state.output_file = "/path/to/nonexistent_report.html"
    mock_kickoff.return_value = mock_flow

    # Act
    run_crew_thread(user_request, log_queue)

    # Assert
    results = list(log_queue.queue)
    assert any(item[0] == "ERROR" and "no output file was found" in item[1] for item in results)
    assert any(item[0] == "END" for item in results)


@patch("epic_news.app.kickoff", side_effect=Exception("Crew failed!"))
def test_run_crew_thread_exception(mock_kickoff):
    """Test the crew thread function when an exception occurs."""
    # Arrange
    log_queue = Queue()
    user_request = "Test request"

    # Act
    run_crew_thread(user_request, log_queue)

    # Assert
    results = list(log_queue.queue)
    assert any(item[0] == "ERROR" and "Crew failed!" in item[1] for item in results)
    assert any(item[0] == "END" for item in results)
