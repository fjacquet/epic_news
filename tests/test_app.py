from queue import Queue
from unittest.mock import MagicMock, mock_open, patch

from epic_news.app import get_session_log_queue, render_html_report, run_crew_thread


@patch("epic_news.app.logger")
def test_session_log_sink_registered_once_per_session(mock_logger):
    """Reruns of the same session must reuse the queue and not add another loguru sink."""
    session_state: dict = {}

    first = get_session_log_queue(session_state)
    second = get_session_log_queue(session_state)

    assert first is second
    mock_logger.add.assert_called_once()


@patch("epic_news.app.logger")
def test_each_session_gets_its_own_log_queue(mock_logger):
    queue_a = get_session_log_queue({})
    queue_b = get_session_log_queue({})

    assert queue_a is not queue_b
    assert mock_logger.add.call_count == 2


@patch("epic_news.app.st")
def test_html_report_fallback_is_not_rendered_unsafely(mock_st):
    render_html_report("<script>alert(1)</script><p>Report</p>")

    mock_st.html.assert_called_once_with("<script>alert(1)</script><p>Report</p>")
    mock_st.markdown.assert_not_called()


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
