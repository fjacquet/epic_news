from queue import Queue
from unittest.mock import MagicMock, patch

from epic_news.app import DOCX_MIME, get_session_log_queue, render_report_download, run_crew_thread


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


def test_docx_mime_type():
    assert DOCX_MIME == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@patch("epic_news.app.st")
def test_report_is_offered_as_a_docx_download_never_as_html(mock_st):
    render_report_download("report.docx", b"PK\x03\x04docx-bytes")

    mock_st.download_button.assert_called_once_with(
        label="Télécharger le rapport (DOCX)",
        data=b"PK\x03\x04docx-bytes",
        file_name="report.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    mock_st.html.assert_not_called()
    mock_st.markdown.assert_not_called()


@patch("epic_news.app.kickoff")
def test_run_crew_thread_success_reads_the_docx_as_bytes(mock_kickoff, tmp_path):
    docx = tmp_path / "report.docx"
    docx.write_bytes(b"PK\x03\x04\xff\xfe binary")
    log_queue = Queue()
    mock_flow = MagicMock()
    mock_flow.state.output_file = str(docx)
    mock_kickoff.return_value = mock_flow

    run_crew_thread("Test request", log_queue)

    results = list(log_queue.queue)
    assert ("REPORT", ("report.docx", b"PK\x03\x04\xff\xfe binary")) in results
    assert any(item[0] == "END" for item in results)
    mock_kickoff.assert_called_once_with(user_input="Test request")


@patch("epic_news.app.kickoff")
@patch("os.path.exists", return_value=False)
def test_run_crew_thread_no_output_file(mock_exists, mock_kickoff):
    """Test the crew thread function when the output file is not found."""
    log_queue = Queue()
    mock_flow = MagicMock()
    mock_flow.state.output_file = "/path/to/nonexistent_report.docx"
    mock_kickoff.return_value = mock_flow

    run_crew_thread("Test request", log_queue)

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
