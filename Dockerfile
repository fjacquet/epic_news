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
# runtime-base — no uv, no git, no build tooling, no dev dependencies.
# ---------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
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
# Every top-level directory the app creates at runtime must be pre-created and
# chowned, because /app itself stays root:root — that is what stops myuser
# rewriting /app/src or /app/.venv. The old single-stage images used
# `chown -R myuser:myuser /app`, which gave that hardening away.
#
# The list is exhaustive as of this change, enumerated from the codebase:
#   db, data, output  — compose bind-mount points
#   traces            — utils/observability.py:29, at MODULE IMPORT time
#   output/dashboard_data — utils/observability.py:30, also at import time
#                           (created inside the myuser-owned output/)
#   checkpoints       — utils/directory_utils.py:28
#   debug             — utils/diagnostics/parsing.py:403, on a diagnostic path
# If a future change adds another bare top-level os.makedirs, startup fails
# loudly with PermissionError and the healthcheck reports unhealthy. Add it
# here rather than widening ownership of /app.
COPY --from=builder --chown=myuser:myuser /app /app
RUN mkdir -p /app/db /app/data /app/output /app/traces /app/checkpoints /app/debug \
    && chown myuser:myuser /app/db /app/data /app/output /app/traces /app/checkpoints /app/debug

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
