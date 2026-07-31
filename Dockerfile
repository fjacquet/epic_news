# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.13-slim-bookworm

# ---------------------------------------------------------------------------
# builder — resolves and installs the venv. Never shipped.
# ---------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS builder

# uv is copied in rather than used as the base image so builder and runtime
# share one interpreter at one path. The venv's python symlinks then resolve
# identically in both stages, which is what the old Dockerfile comments about
# "two interpreters" and "Permission denied" were guarding against.
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# git resolves the crewai-custom-tools git+https dependency. Builder only.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency layer. The manifests are bind-mounted, so they never become a
# layer, and this step is invalidated only by a lockfile or manifest change —
# not by a source edit.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Source layer. The manifests are bind-mounted again because the previous
# mount did not persist them into /app, and building the project needs them.
COPY src/ ./src
COPY templates/ ./templates
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev

# ---------------------------------------------------------------------------
# runtime-base — no git, no compiler, no dev dependencies. `uv` and `uvx` are
# deleted below rather than never installed: they arrive inside the venv via
# crewai-cli, a *main* dependency of crewai, so `--no-dev` cannot drop them.
#
# `pip` and `pip3` DO remain, at /usr/local/bin, because the python base image
# ships them. They point at the system interpreter (/usr/local/bin/python3.13),
# not at the venv, and both /usr/local and the venv are root-owned while the
# container runs as myuser — so they cannot write to either. `--user` installs
# land in $HOME but stay invisible to the app: the venv reports
# ENABLE_USER_SITE=False, and the venv interpreter has no pip module at all.
# This is a reduced runtime, not a sealed one; do not read it as more.
#
# Verify with a loop, never `command -v a b c` — that form only evaluates its
# FIRST operand, so a single absent binary makes it "pass" for all of them:
#   docker run --rm <img> sh -c \
#     'for b in git uv uvx; do command -v "$b" && echo "FAIL_PRESENT $b"; done; echo CHECK_DONE'
# ---------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH

# WeasyPrint runtime libraries, imported by tools/html_to_pdf_tool.py.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m myuser

WORKDIR /app

# COPY before mkdir: a COPY into an existing /app merges rather than replaces,
# so creating the data directories first would leave ownership unpredictable.
#
# There are deliberately no VOLUME declarations. The old Dockerfiles declared
# VOLUME on these paths, which makes Docker create a root-owned anonymous
# volume on every run — unwritable by myuser, and leaked to disk. compose
# bind-mounts host paths over them instead. Do not reintroduce VOLUME here.
#
# The COPY carries NO --chown. That is the point: --chown applies recursively,
# so chowning here would hand /app/src and /app/.venv to myuser and the runtime
# user could rewrite its own code and interpreter. Left root-owned, they are
# read-only to myuser. Nothing writes to them at runtime — UV_COMPILE_BYTECODE
# precompiles in the builder and PYTHONDONTWRITEBYTECODE blocks runtime .pyc.
#
# Root-owned /app also prevents myuser creating or deleting entries directly
# under /app. So every top-level directory the app writes to must be created
# and chowned here, up front. Enumerated from the codebase by sweeping for both
# `os.makedirs(` and `.mkdir(` — the second form is easy to miss:
#   db, data, output  — compose bind-mount points
#   traces            — utils/observability.py:29, at MODULE IMPORT time
#   output/dashboard_data — utils/observability.py:30, also at import time
#                           (lands inside the myuser-owned output/)
#   checkpoints       — utils/directory_utils.py:28
#   debug             — utils/diagnostics/parsing.py:403, diagnostic path
#   logs              — utils/logger.py:38, via setup_logging(), which is the
#                       FIRST statement of kickoff() in main.py
#
# A missing entry does not always fail loudly. `traces` breaks at import and
# the healthcheck catches it; `logs` breaks inside a FastAPI BackgroundTask
# after /kickoff has already returned 202, on a container that stays healthy.
# Add new directories here rather than widening ownership of /app.
#
# This is ONE COPY, and splitting it into `.venv` / `src` / `templates` was
# tried and measured and does NOT work. The theory was that a source edit would
# leave a lockfile-keyed venv layer CACHED instead of re-pushing 1.52 GB. It
# does not, because the venv is not source-independent. The project is an
# editable install, so `uv sync` reinstalls it on every source change and
# rewrites its install metadata inside the venv —
# `.venv/lib/python3.13/site-packages/epic_news-*.dist-info/uv_cache.json`,
# which records an mtime for the source tree:
#   {"directories":{"src":{"secs_since_epoch":...,"nanos_since_epoch":...}}}
# — plus RECORD, which hashes it. Those two files were the only content that
# differed between builds, and it was enough: `COPY --from=builder /app/.venv`
# missed cache (13.8s, new layer digest) after a one-line edit to api.py. A
# no-change rebuild is fully CACHED, so the miss is caused by the edit, not by
# build nondeterminism.
# Defeating this needs a separate deps-only venv stage, not a COPY split.
COPY --from=builder /app /app

# uv and uvx are installed *into the venv* by crewai-cli. Nothing at runtime
# shells out to them: all three CMDs and both supervisord programs invoke
# absolute venv paths, and no source file spawns uv as a subprocess.
#
# This removes them from the running container's filesystem, not from the
# image: a whiteout in a later layer cannot delete bytes from the layer below,
# so the binaries are still recoverable by anyone who can unpack the layers,
# and the image does not shrink. It closes "the running process can invoke
# uv", which is the threat that matters here. It is not a scrub.
RUN rm -f /app/.venv/bin/uv /app/.venv/bin/uvx

RUN mkdir -p /app/db /app/data /app/output /app/traces /app/checkpoints /app/debug /app/logs \
    && chown myuser:myuser /app/db /app/data /app/output /app/traces /app/checkpoints /app/debug /app/logs

# ---------------------------------------------------------------------------
# api
# ---------------------------------------------------------------------------
FROM runtime-base AS api

EXPOSE 8000

# curl is not installed in the slim base, and installing it just to probe an
# HTTP endpoint would add a package for something the interpreter already does.
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status == 200 else 1)"]

USER myuser
CMD ["uvicorn", "epic_news.api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

# ---------------------------------------------------------------------------
# streamlit
# ---------------------------------------------------------------------------
FROM runtime-base AS streamlit

EXPOSE 8501

# /_stcore/health is Streamlit's current health path. /healthz is the legacy
# one the old Dockerfile used.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5).status == 200 else 1)"]

USER myuser
CMD ["streamlit", "run", "src/epic_news/app.py", "--server.port=8501", "--server.headless=true", "--server.address=0.0.0.0"]

# ---------------------------------------------------------------------------
# combined — both apps under supervisor, still non-root.
# ---------------------------------------------------------------------------
FROM runtime-base AS combined

RUN apt-get update && apt-get install -y --no-install-recommends supervisor \
    && rm -rf /var/lib/apt/lists/*

# No --chown: root-owned 0644 is readable by supervisord running as myuser, and
# it denies the runtime user a rewrite-the-config-then-reload path. That is also
# what defuses the [unix_http_server]/[supervisorctl] sections in the file —
# they are worth keeping for debugging a two-process container, but only while
# the config they would act on cannot be edited from inside.
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=15s --start-period=45s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; api = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status; ui = urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5).status; sys.exit(0 if api == 200 and ui == 200 else 1)"]

USER myuser
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
