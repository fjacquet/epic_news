import logging
import os
from queue import Empty, Queue
from threading import Thread

import streamlit as st

from epic_news.main import kickoff

# --- Streamlit UI Configuration ---
st.set_page_config(page_title="Epic News CrewAI Orchestrator", layout="wide")
st.title("✨ Epic News CrewAI Orchestrator")
st.markdown("""Welcome! Enter your request below, and the `ReceptionFlow` will automatically classify it
and dispatch the appropriate crew to handle the job.""")

# --- State Management ---
if "crew_running" not in st.session_state:
    st.session_state.crew_running = False
if "log_messages" not in st.session_state:
    st.session_state.log_messages = []
if "final_report" not in st.session_state:
    st.session_state.final_report = None


# --- Real-time Logging Setup ---
class QueueLogger(logging.Handler):
    """A custom logging handler that puts messages into a queue."""

    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        self.queue.put(self.format(record))


log_queue = Queue()
queue_handler = QueueLogger(log_queue)
# You can customize the formatter for a cleaner look in the UI
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
queue_handler.setFormatter(formatter)

# Add the handler to the root logger to capture logs from crewai and other libs
logging.basicConfig(level=logging.INFO, handlers=[queue_handler])


# --- Crew Execution Logic ---
def run_crew_thread(user_request: str):
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
        logging.error(f"An error occurred in the crew thread: {e}", exc_info=True)
        log_queue.put(("ERROR", str(e)))
    finally:
        log_queue.put(("END", "Crew execution finished."))


# --- UI Components ---
user_request = st.text_input(
    "Enter your request",
    "Summarize 'Art of War by Sun Tzu' and suggest similar books.",
    disabled=st.session_state.crew_running,
)

if st.button("🚀 Kickoff Flow", disabled=st.session_state.crew_running):
    # Reset state for a new run
    st.session_state.crew_running = True
    st.session_state.log_messages = []
    st.session_state.final_report = None
    st.rerun()

# --- Display Logic for Running Crew ---
if st.session_state.crew_running:
    st.info("ReceptionFlow is running... Logs will appear below.")
    log_placeholder = st.empty()
    report_placeholder = st.empty()

    # Start the crew thread only on the first run
    if "thread" not in st.session_state or not st.session_state.thread.is_alive():
        st.session_state.thread = Thread(target=run_crew_thread, args=(user_request,))
        st.session_state.thread.start()

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

            # Update the log display
            log_placeholder.code("\n".join(st.session_state.log_messages), language="log")

        except Empty:
            continue  # Continue polling

    # Final state update after loop
    st.session_state.crew_running = False
    if st.session_state.final_report:
        report_placeholder.success("Crew finished! Here is the final report:")
        st.markdown(st.session_state.final_report, unsafe_allow_html=True)
    else:
        report_placeholder.error("Crew finished, but no report was generated.")

    # Clean up the thread
    del st.session_state["thread"]
    st.rerun()  # Rerun to reset the UI to its initial state
