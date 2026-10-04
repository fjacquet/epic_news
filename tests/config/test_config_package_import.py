import subprocess
import sys


def test_importing_config_does_not_import_composio():
    code = "import sys; import epic_news.config.llm_config; print('composio' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"


def test_importing_main_does_not_import_composio():
    code = "import sys; import epic_news.main; print('composio' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"
