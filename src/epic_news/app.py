import os
from queue import Empty, Queue
from threading import Thread

import streamlit as st
from loguru import logger

from epic_news.main import kickoff

# --- Streamlit UI Configuration ---
st.set_page_config(page_title="Epic News CrewAI Orchestrator", layout="wide")
st.title("✨ Epic News CrewAI Orchestrator")
st.markdown("""Welcome! Enter your research question below. The system will classify it
and dispatch the appropriate crew to handle the job.""")

# --- State Management ---
if "crew_running" not in st.session_state:
    st.session_state.crew_running = False
if "log_messages" not in st.session_state:
    st.session_state.log_messages = []
if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "final_report_md" not in st.session_state:
    st.session_state.final_report_md = None


# --- Real-time Logging Setup ---
class StreamlitLogSink:
    """A custom logging sink that puts messages into a queue."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def __call__(self, message):
        self.queue.put(message.strip())


log_queue = Queue()
logger.add(StreamlitLogSink(log_queue), format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")


# --- Helpers ---
def html_to_markdown(html: str) -> str:
    """Best-effort HTML→Markdown conversion for displaying/downloading.

    Tries `markdownify` if available; falls back to BeautifulSoup text extraction;
    finally returns original HTML if no converters are available.
    """
    try:
        # Prefer markdownify when present
        from markdownify import markdownify as md  # type: ignore

        return md(html, heading_style="ATX")
    except Exception:
        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(html, "html.parser")
            # Keep basic structure using newlines
            text = soup.get_text("\n")
            return text.strip()
        except Exception:
            return html


# --- Crew Execution Logic ---
def run_crew_thread(user_request: str, log_queue: Queue):
    """Runs the ReceptionFlow in a separate thread to avoid blocking the UI."""
    try:
        # The kickoff function will run the flow. The flow's state will hold the output path.
        flow = kickoff(user_input=user_request)

        # After running, put the result into the queue
        if flow and flow.state.output_file and os.path.exists(flow.state.output_file):
            with open(flow.state.output_file, encoding="utf-8") as f:
                report_content = f.read()
            log_queue.put(("REPORT", report_content))
        else:
            error_message = f"Flow finished, but no output file was found at '{flow.state.output_file if flow else 'N/A'}'"
            log_queue.put(("ERROR", error_message))

    except Exception as e:
        logger.error(f"An error occurred in the crew thread: {e}", exc_info=True)
        log_queue.put(("ERROR", str(e)))
    finally:
        log_queue.put(("END", "Crew execution finished."))


# --- UI Components ---
user_request = st.text_input(
    "Enter your research question",
    "Summarize 'Art of War by Sun Tzu' and suggest similar books.",
    disabled=st.session_state.crew_running,
)

if st.button("🔎 Start Research", disabled=st.session_state.crew_running):
    # Reset state for a new run
    st.session_state.crew_running = True
    st.session_state.log_messages = []
    st.session_state.final_report = None
    st.session_state.final_report_md = None

    # Start the crew thread
    st.session_state.thread = Thread(target=run_crew_thread, args=(user_request, log_queue))
    st.session_state.thread.start()

# --- Display Logic for Running Crew ---
if st.session_state.crew_running:
    with st.status("ReceptionFlow is running...", expanded=True) as status:
        log_placeholder = st.empty()

        # Poll the queue for updates
        while st.session_state.thread.is_alive() or not log_queue.empty():
            try:
                message = log_queue.get(timeout=0.1)
                if isinstance(message, tuple):
                    msg_type, content = message
                    if msg_type == "REPORT":
                        st.session_state.final_report = content
                    elif msg_type == "ERROR":
                        st.session_state.log_messages.append(f"❌ ERROR: {content}")
                    elif msg_type == "END":
                        st.session_state.crew_running = False
                        break  # Exit the loop
                else:
                    st.session_state.log_messages.append(message)

                # Update the log display inside the status box
                log_placeholder.code("\n".join(st.session_state.log_messages), language="log")

            except Empty:
                continue  # Continue polling

        # Final state update after loop
        st.session_state.crew_running = False
        if st.session_state.final_report:
            st.session_state.final_report_md = html_to_markdown(st.session_state.final_report)
            status.update(label="✅ Crew finished! Final report is ready.", state="complete")
        else:
            status.update(label="❌ Crew finished, but no report was generated.", state="error")

    # After status closes, show the final report section and download
    if st.session_state.final_report_md:
        st.subheader("Final Report (Markdown)")
        st.markdown(st.session_state.final_report_md)

        # Suggest a filename based on output_file if available
        default_name = "final_report.md"
        try:
            if "thread" in st.session_state and hasattr(st.session_state, "thread"):
                pass  # no-op; kept for symmetry
            # We cannot access flow object here; rely on a default name
        except Exception:
            pass

        st.download_button(
            label="⬇️ Download report (.md)",
            data=st.session_state.final_report_md,
            file_name=default_name,
            mime="text/markdown",
        )
    elif st.session_state.final_report:
        # Fallback: if markdown conversion failed, still show HTML
        st.subheader("Final Report (HTML)")
        st.markdown(st.session_state.final_report, unsafe_allow_html=True)

    # Clean up the thread
    if "thread" in st.session_state:
        del st.session_state["thread"]
