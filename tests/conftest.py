import atexit
import os
import shutil
import tempfile

from epic_news.utils import observability

# crewai-custom-tools >=0.4.0: PerplexitySearchTool fails fast at construction
# without a key. CI has no .env; give the suite a dummy so construction-time
# wiring works. Tests that verify missing-key behavior monkeypatch.delenv.
os.environ.setdefault("PERPLEXITY_API_KEY", "test-key")

# The flow and company_news build their Tracer at import, under TRACE_DIR. Point it
# at a temp dir before any test module imports them, so tests never write to traces/.
observability.TRACE_DIR = tempfile.mkdtemp(prefix="epic-news-traces-")
atexit.register(shutil.rmtree, observability.TRACE_DIR, ignore_errors=True)
