from queue import Queue
from unittest.mock import patch

from epic_news.app import DOCX_MIME, get_session_log_queue, render_report_download, run_crew_thread
from epic_news.main import ReceptionFlow


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


def _flow_kickoff_writing(output_file: str):
    """Stand-in for ReceptionFlow.kickoff: the real flow leaves the report path on its state."""

    def _kickoff(self):
        self.state.output_file = output_file

    return _kickoff


def test_run_crew_thread_reads_the_report_path_from_the_flow_it_ran(tmp_path):
    """The app runs ReceptionFlow itself and reads state.output_file from that flow.

    Only ReceptionFlow.kickoff is patched, so the path from the flow object to the
    download is the real one (main.kickoff() returns None and cannot carry it).
    """
    docx = tmp_path / "report.docx"
    docx.write_bytes(b"PK\x03\x04\xff\xfe binary")
    log_queue: Queue = Queue()

    with patch.object(
        ReceptionFlow, "kickoff", autospec=True, side_effect=_flow_kickoff_writing(str(docx))
    ) as mock_kickoff:
        run_crew_thread("Test request", log_queue)

    results = list(log_queue.queue)
    assert ("REPORT", ("report.docx", b"PK\x03\x04\xff\xfe binary")) in results
    assert any(item[0] == "END" for item in results)
    flow = mock_kickoff.call_args.args[0]
    assert isinstance(flow, ReceptionFlow)
    assert flow._user_request == "Test request"


def test_run_crew_thread_no_output_file(tmp_path):
    """A flow that ends without a report file is reported as an error, never as a download."""
    log_queue: Queue = Queue()
    missing = tmp_path / "nonexistent_report.docx"

    with patch.object(
        ReceptionFlow, "kickoff", autospec=True, side_effect=_flow_kickoff_writing(str(missing))
    ):
        run_crew_thread("Test request", log_queue)

    results = list(log_queue.queue)
    assert not any(item[0] == "REPORT" for item in results)
    assert any(item[0] == "ERROR" and "no output file was found" in item[1] for item in results)
    assert any(item[0] == "END" for item in results)


def test_run_crew_thread_exception():
    """A flow that raises is reported as an error."""
    log_queue: Queue = Queue()

    with patch.object(ReceptionFlow, "kickoff", autospec=True, side_effect=Exception("Crew failed!")):
        run_crew_thread("Test request", log_queue)

    results = list(log_queue.queue)
    assert any(item[0] == "ERROR" and "Crew failed!" in item[1] for item in results)
    assert any(item[0] == "END" for item in results)
