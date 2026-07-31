# Docker Build Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace three single-stage Dockerfiles with one multi-stage `Dockerfile` exposing `api`, `streamlit` and `combined` targets, so that source edits stop invalidating the dependency layer, dev tooling stops reaching production images, and healthchecks actually pass.

**Architecture:** A `builder` stage installs the venv with `uv` using BuildKit bind mounts for the manifests and a cache mount for uv's download cache. A `runtime-base` stage on the *identical* Python image copies only `/app` from the builder — no `uv`, no `git`, no dev dependencies. Three thin target stages differ only in exposed port, healthcheck and `CMD`.

**Tech Stack:** Docker BuildKit (`# syntax=docker/dockerfile:1`), `uv` 0.12, Python 3.13, FastAPI, Streamlit 1.60, supervisor, GitHub Actions `docker/build-push-action@v7`.

**Source spec:** `docs/superpowers/specs/2026-07-30-docker-build-restructure-design.md`

## Global Constraints

- Package manager is `uv` only. Never `pip`, `poetry`, or `pipenv`.
- Python 3.13 (`requires-python = ">=3.13,<3.14"`). Both build stages use `python:3.13-slim-bookworm`.
- Prefix shell commands with `rtk` where a filter exists (`rtk git ...`). RTK mangles pytest and `gh --json` output — run those plain.
- Run tests with `uv run pytest`. If pytest is missing, the venv was pruned: `uv sync --all-extras`.
- Modern union syntax (`X | None`) in Python. Loguru, not `logging`.
- Commit messages end with `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Never `git add -A`. Stage explicitly — `src/epic_news/main.py` is a personal sentinel file and must never be committed by this work.
- `Dockerfile.code-interpreter` is **out of scope** — do not modify or delete it.
  Its workflow is out of scope too, with one exception forced by Task 6: it built
  from the now-deleted `Dockerfile.streamlit`, so Task 8 Step 4 repoints that one
  line. Nothing else in it changes.
- Image size is **not** a success criterion. Do not prune dependencies, do not split `pyproject.toml` into extras.

## Verified constants

Do not re-derive these; they were confirmed against the codebase and library docs during planning.

| Constant | Value | Source |
| --- | --- | --- |
| Streamlit health endpoint | `/_stcore/health` | Streamlit official Docker deployment docs via context7; locked version is 1.60.0 |
| API health endpoint | `/health` | **Does not exist yet** — created in Task 1 |
| uv image tag | `ghcr.io/astral-sh/uv:0.12` | Matches locally installed uv 0.12.0 |
| Runtime apt packages | `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libgdk-pixbuf-2.0-0 shared-mime-info` | WeasyPrint, imported by `src/epic_news/tools/html_to_pdf_tool.py` |
| Builder-only apt package | `git` | `crewai-custom-tools` is a `git+https` dependency |
| Non-root user | `myuser` | Preserved from the existing Dockerfiles |

## File Structure

| File | Action | Responsibility |
| --- | --- | --- |
| `src/epic_news/api.py` | Modify | Add the `GET /health` route the healthchecks depend on |
| `tests/test_api.py` | Modify | Cover the new route |
| `.dockerignore` | Rewrite | Allowlist the build context |
| `Dockerfile` | Create | All three images: `builder`, `runtime-base`, `api`, `streamlit`, `combined` |
| `Dockerfile.api` | Delete | Superseded by the `api` target |
| `Dockerfile.streamlit` | Delete | Superseded by the `streamlit` target |
| `Dockerfile.combined` | Delete | Superseded by the `combined` target |
| `supervisord.conf` | Modify | Non-root operation, venv absolute paths |
| `docker-compose.yml` | Modify | Working healthchecks |
| `docker-compose.api.yml` | Modify | Build target + working healthcheck |
| `docker-compose.streamlit.yml` | Modify | Build target + working healthcheck (legacy `/healthz` path) |
| `Makefile` | Modify | Three `docker-build-*` targets retargeted |
| `.github/workflows/docker-publish-{api,streamlit,combined}.yml` | Modify | `target:` + shared cache scope |
| `.github/workflows/docker-publish-code-interpreter.yml` | Modify | One line: build from `Dockerfile.code-interpreter`, not the deleted `Dockerfile.streamlit` |

---

## Task 1: Add the `/health` route to the API

The spec assumed this route existed. It does not — `src/epic_news/api.py` defines only `POST /kickoff`. Every healthcheck in this plan targets `/health`, so this must land first or every later verification fails with a 404.

**Files:**
- Modify: `src/epic_news/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `GET /health` returning HTTP 200 with body `{"status": "ok"}`. Tasks 3, 5, 7 depend on this exact path and status code.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api.py`:

```python
def test_health_endpoint():
    """The container HEALTHCHECK and docker-compose both probe this route."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api.py::test_health_endpoint -v`

Expected: FAIL with `assert 404 == 200`.

- [ ] **Step 3: Write the minimal implementation**

In `src/epic_news/api.py`, insert after the `KickoffRequest` class definition and before `kickoff_endpoint`:

```python
@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe for the container HEALTHCHECK and docker-compose.

    Deliberately does no dependency checking: it answers "is the ASGI app
    accepting requests", not "is every downstream provider reachable".
    """
    return {"status": "ok"}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_api.py -v`

Expected: PASS, all three tests in the file green.

- [ ] **Step 5: Lint**

Run: `uv run ruff format src/epic_news/api.py tests/test_api.py && uv run ruff check --fix src/epic_news/api.py tests/test_api.py`

Expected: no remaining violations.

- [ ] **Step 6: Commit**

```bash
rtk git add src/epic_news/api.py tests/test_api.py
rtk git commit -m "$(cat <<'EOF'
feat(api): add GET /health liveness route

Container healthchecks and docker-compose both probe /health, which did
not exist — they would have 404'd even once curl was available.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Rewrite `.dockerignore` as an allowlist

`src/epic_news/crews/.mypy_cache/` is 234 MB and ships in every image today, because the current denylist has a rule for `.pytest_cache/` but nobody added one for `.mypy_cache`. Inverting to an allowlist closes the whole class of hole.

**Files:**
- Modify: `.dockerignore`

**Interfaces:**
- Consumes: nothing.
- Produces: a build context containing only `pyproject.toml`, `uv.lock`, `src/`, `templates/`, `supervisord.conf`. Task 3's `COPY src/ ./src` relies on `src/**/.mypy_cache/` being excluded.

- [ ] **Step 1: Measure the current context size**

Write the probe Dockerfile to the scratchpad (not the repo):

```bash
printf 'FROM busybox\nCOPY . /ctx\nRUN du -sh /ctx\n' > /tmp/ctx-probe.Dockerfile
docker build --no-cache --progress=plain -f /tmp/ctx-probe.Dockerfile . 2>&1 | grep -E "transferring context|/ctx"
```

Expected: a `transferring context` line in the hundreds of megabytes. Record the number.

- [ ] **Step 2: Replace `.dockerignore` entirely**

```
# Allowlist, not a denylist.
#
# A denylist let src/epic_news/crews/.mypy_cache (234 MB) into every published
# image, because nobody added a rule for it. Excluding everything by default
# means a new junk directory cannot leak in without someone explicitly
# allowing it.

*

!pyproject.toml
!uv.lock
!src/
!templates/
!supervisord.conf

# Junk nested inside the allowed trees. Later patterns win, so these re-exclude
# from within the re-included directories above.
src/**/__pycache__/
src/**/.mypy_cache/
src/**/.pytest_cache/
src/**/.ruff_cache/
src/**/*.egg-info/
templates/**/__pycache__/
```

- [ ] **Step 3: Re-measure and confirm the drop**

```bash
docker build --no-cache --progress=plain -f /tmp/ctx-probe.Dockerfile . 2>&1 | grep -E "transferring context|/ctx"
```

Expected: `transferring context` under 2 MB, and the `du -sh /ctx` line confirming a small tree.

- [ ] **Step 4: Confirm the required build inputs survived**

```bash
docker build --no-cache -q -f /tmp/ctx-probe.Dockerfile -t ctx-probe . >/dev/null
docker run --rm ctx-probe sh -c "ls /ctx && test -f /ctx/pyproject.toml && test -f /ctx/uv.lock && test -f /ctx/supervisord.conf && test -d /ctx/src/epic_news && test -d /ctx/templates && echo ALL_INPUTS_PRESENT"
docker run --rm ctx-probe sh -c "test ! -d /ctx/src/epic_news/crews/.mypy_cache && echo MYPY_CACHE_EXCLUDED"
```

Expected: both `ALL_INPUTS_PRESENT` and `MYPY_CACHE_EXCLUDED` printed. If `ALL_INPUTS_PRESENT` is missing, a `!` line is wrong; do not proceed to Task 3.

- [ ] **Step 5: Clean up the probe**

```bash
docker rmi ctx-probe
```

- [ ] **Step 6: Commit**

```bash
rtk git add .dockerignore
rtk git commit -m "$(cat <<'EOF'
build(docker): invert .dockerignore to an allowlist

A denylist shipped a 234 MB mypy cache in every image. Excluding
everything by default means new junk cannot leak in silently.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Create the multi-stage `Dockerfile` with the `api` target

**Files:**
- Create: `Dockerfile`

**Interfaces:**
- Consumes: `GET /health` from Task 1; the allowlist context from Task 2.
- Produces: stages named `builder`, `runtime-base`, `api`. Tasks 4 and 5 add targets that are `FROM runtime-base`. Task 8's workflows pass `target: api`.

- [ ] **Step 1: Write the Dockerfile**

Create `Dockerfile` at the repo root:

```dockerfile
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
COPY --from=builder /app /app
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
```

- [ ] **Step 2: Build the api target**

Run: `docker build --target api -t epic_news-api:latest .`

Expected: build succeeds. If it fails at the second `uv sync` with a missing `pyproject.toml`, the bind mounts on that step were dropped — they are required.

- [ ] **Step 3: Verify the build tooling did not reach the image**

```bash
docker run --rm epic_news-api:latest sh -c 'for b in git uv uvx; do command -v "$b" && echo "FAIL_PRESENT $b"; done; echo CHECK_DONE'
docker run --rm epic_news-api:latest sh -c 'python -c "import mypy" 2>&1 | tail -1'
docker run --rm epic_news-api:latest sh -c 'python -c "import pytest" 2>&1 | tail -1'
docker run --rm epic_news-api:latest id -u
```

Single-quote these so `$?` and friends are evaluated inside the container, not by the host shell.

Loop over the binaries one at a time. Do NOT write `command -v git uv uvx` — that
form evaluates only its FIRST operand, so one absent binary makes the whole check
"pass". It is what hid `uv` (0.11.30, pulled in by `crewai-cli`, a main dependency
of `crewai`) in every runtime image through an entire review round.

Expected: `CHECK_DONE` with no `FAIL_PRESENT` line before it; two
`ModuleNotFoundError` lines; `id -u` prints a non-zero UID (not `0`).
`pip`/`pip3` are deliberately NOT in the loop — they belong to the python base
image and stay.

- [ ] **Step 3b: Verify the filesystem permission split**

Exercising this through `POST /kickoff` would run a real crew against live LLM
APIs, so probe the permissions directly instead. Every directory the app writes
to must be writable, and the code and interpreter must not be.

```bash
docker run --rm epic_news-api:latest sh -c '
for d in db data output traces checkpoints debug logs; do
  touch "/app/$d/.probe" 2>/dev/null && echo "WRITABLE  $d" || echo "FAIL_RO   $d"
done
touch /app/src/epic_news/api.py 2>/dev/null && echo "FAIL_RW   src" || echo "READONLY  src"
touch /app/.venv/bin/uvicorn  2>/dev/null && echo "FAIL_RW   .venv" || echo "READONLY  .venv"
touch /app/.probe             2>/dev/null && echo "FAIL_RW   /app" || echo "READONLY  /app"
'
```

Expected: seven `WRITABLE` lines, then `READONLY src`, `READONLY .venv`,
`READONLY /app`. Any `FAIL_` line is a real failure — a `FAIL_RO` means the app
will crash or silently lose logs at runtime, a `FAIL_RW` means the hardening
this task exists for is not in place.

- [ ] **Step 4: Verify the app runs and reaches `healthy`**

```bash
docker run -d --name epic-api-test -p 8000:8000 epic_news-api:latest
sleep 30
docker inspect --format '{{.State.Health.Status}}' epic-api-test
curl -sf http://127.0.0.1:8000/health
docker rm -f epic-api-test
```

Expected: health status `healthy`, and `{"status":"ok"}` from curl. This is the first time any image in this repo has reported healthy.

- [ ] **Step 5: Verify the dependency layer survives a source edit**

```bash
touch src/epic_news/api.py
docker build --target api --progress=plain -t epic_news-api:latest . 2>&1 | grep -E "uv sync --locked --no-install-project|CACHED"
```

Expected: the `--no-install-project` step shows `CACHED`. If it re-runs, the layer ordering is wrong.

- [ ] **Step 6: Verify WeasyPrint still works with the reduced apt list**

```bash
docker run --rm epic_news-api:latest python -c "
from weasyprint import HTML
HTML(string='<h1>probe</h1>').write_pdf('/tmp/probe.pdf')
print('PDF_OK')
"
```

Expected: `PDF_OK`. A missing shared library here means an apt package was dropped that WeasyPrint needs.

- [ ] **Step 7: Commit**

```bash
rtk git add Dockerfile
rtk git commit -m "$(cat <<'EOF'
build(docker): add multi-stage Dockerfile with api target

Builder installs the venv with bind-mounted manifests and a uv cache
mount, so source edits no longer invalidate the dependency layer.
Runtime carries no uv, no git and no dev dependencies, and its
healthcheck uses the interpreter instead of an uninstalled curl.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Add the `streamlit` target

**Files:**
- Modify: `Dockerfile`

**Interfaces:**
- Consumes: the `runtime-base` stage from Task 3.
- Produces: a stage named `streamlit`. Task 8's workflow passes `target: streamlit`.

- [ ] **Step 1: Append the target to `Dockerfile`**

```dockerfile

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
```

- [ ] **Step 2: Build the streamlit target**

Run: `docker build --target streamlit -t epic_news-streamlit:latest .`

Expected: succeeds, and the builder stages report `CACHED` — proof the shared builder pays off.

- [ ] **Step 3: Verify it runs and reaches `healthy`**

```bash
docker run -d --name epic-st-test -p 8501:8501 epic_news-streamlit:latest
sleep 40
docker inspect --format '{{.State.Health.Status}}' epic-st-test
curl -sf http://127.0.0.1:8501/_stcore/health
curl -sf -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8501/
docker rm -f epic-st-test
```

Expected: health status `healthy`, `ok` from the health path, and `200` from the app root.

- [ ] **Step 4: Verify test extras were not installed**

The old `Dockerfile.streamlit` used `--all-extras`, whose only group is `test`.

```bash
docker run --rm epic_news-streamlit:latest python -c "import faker" ; echo "faker import exit=$?"
docker run --rm epic_news-streamlit:latest id -u
```

Expected: `ModuleNotFoundError` with a non-zero exit, and a non-zero UID.

- [ ] **Step 5: Commit**

```bash
rtk git add Dockerfile
rtk git commit -m "$(cat <<'EOF'
build(docker): add streamlit target

Shares the builder stage with api. Drops --all-extras, whose only group
is test, and probes /_stcore/health rather than the legacy /healthz.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Add the `combined` target and de-root supervisord

**Files:**
- Modify: `Dockerfile`
- Modify: `supervisord.conf`

**Interfaces:**
- Consumes: `runtime-base` from Task 3; `GET /health` from Task 1; `/_stcore/health` from Task 4.
- Produces: a stage named `combined`. Task 8's workflow passes `target: combined`.

- [ ] **Step 1: Rewrite `supervisord.conf`**

Replace the file entirely. Both `command=` lines change from `uv run --no-cache ...` to absolute venv paths, because `uv` does not exist in the runtime image. The socket and pidfile move to `/tmp` so nothing needs to write to `/var/run` as root, and `user=myuser` is removed from each program because supervisord itself is no longer root and cannot setuid.

```ini
[supervisord]
nodaemon=true
pidfile=/tmp/supervisord.pid
logfile=/dev/null
logfile_maxbytes=0

[unix_http_server]
file=/tmp/supervisor.sock
chmod=0700

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[program:fastapi]
command=/app/.venv/bin/uvicorn epic_news.api:app --host 0.0.0.0 --port 8000 --proxy-headers
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=HOME="/home/myuser"

[program:streamlit]
command=/app/.venv/bin/streamlit run src/epic_news/app.py --server.port 8501 --server.headless=true --server.address 0.0.0.0
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=HOME="/home/myuser"
```

- [ ] **Step 2: Append the target to `Dockerfile`**

`supervisor` is installed before `USER myuser` because apt requires root.

```dockerfile

# ---------------------------------------------------------------------------
# combined — both apps under supervisor, still non-root.
# ---------------------------------------------------------------------------
FROM runtime-base AS combined

RUN apt-get update && apt-get install -y --no-install-recommends supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=myuser:myuser supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=15s --start-period=45s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; api = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status; ui = urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5).status; sys.exit(0 if api == 200 and ui == 200 else 1)"]

USER myuser
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

- [ ] **Step 3: Build the combined target**

Run: `docker build --target combined -t epic_news-combined:latest .`

Expected: succeeds; builder stages `CACHED`.

- [ ] **Step 4: Verify both apps run under a non-root supervisord**

```bash
docker run -d --name epic-combined-test -p 8000:8000 -p 8501:8501 epic_news-combined:latest
sleep 50
docker inspect --format '{{.State.Health.Status}}' epic-combined-test
docker exec epic-combined-test id -u
docker exec epic-combined-test supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status
curl -sf http://127.0.0.1:8000/health
curl -sf http://127.0.0.1:8501/_stcore/health
docker rm -f epic-combined-test
```

Expected: health status `healthy`; `id -u` non-zero; `supervisorctl status` lists both `fastapi` and `streamlit` as `RUNNING`; both curls succeed.

If supervisord exits complaining it cannot write its pidfile or socket, a `/tmp` path in `supervisord.conf` was missed.

- [ ] **Step 5: Commit**

```bash
rtk git add Dockerfile supervisord.conf
rtk git commit -m "$(cat <<'EOF'
build(docker): add combined target, drop root from supervisord

supervisord ran as root purely to setuid each program. Moving its socket
and pidfile to /tmp lets the whole process tree run as myuser. Program
commands use absolute venv paths since uv is no longer in the runtime.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Delete the old Dockerfiles and retarget the Makefile

Only safe once all three targets have been verified in Tasks 3 to 5.

**Files:**
- Delete: `Dockerfile.api`, `Dockerfile.streamlit`, `Dockerfile.combined`
- Modify: `Makefile:157-167`

**Interfaces:**
- Consumes: the three verified targets.
- Produces: `make docker-build-api|docker-build-streamlit|docker-build-combined` building from `Dockerfile` via `--target`.

- [ ] **Step 1: Delete the three superseded Dockerfiles**

```bash
rtk git rm Dockerfile.api Dockerfile.streamlit Dockerfile.combined
```

`Dockerfile.code-interpreter` stays. Do not remove it.

- [ ] **Step 2: Retarget the Makefile build rules**

In `Makefile`, replace the three recipe lines (leave `docker-build-code-interpreter` and `docker-build-all` untouched):

```makefile
docker-build-api: ## Build FastAPI Docker image
	@echo "$(GREEN)Building FastAPI image...$(RESET)"
	$(DOCKER) build -f Dockerfile --target api -t $(PROJECT_NAME)-api:latest .

docker-build-streamlit: ## Build Streamlit Docker image
	@echo "$(GREEN)Building Streamlit image...$(RESET)"
	$(DOCKER) build -f Dockerfile --target streamlit -t $(PROJECT_NAME)-streamlit:latest .

docker-build-combined: ## Build combined Docker image
	@echo "$(GREEN)Building combined image...$(RESET)"
	$(DOCKER) build -f Dockerfile --target combined -t $(PROJECT_NAME)-combined:latest .
```

Recipe lines must be indented with a literal tab, not spaces.

- [ ] **Step 3: Verify each Makefile target builds**

```bash
make docker-build-api && make docker-build-streamlit && make docker-build-combined
```

Expected: all three succeed. `make docker-build-all` will additionally build the untouched code-interpreter image; that is expected and unchanged.

- [ ] **Step 4: Confirm nothing still references the deleted files**

```bash
rtk grep -rn "Dockerfile.api\|Dockerfile.streamlit\|Dockerfile.combined" . --include=Makefile --include=*.yml --include=*.yaml --include=*.md
```

Expected: hits in `docker-compose.api.yml` and `docker-compose.streamlit.yml` (Task 7), the workflows (Task 8), and documentation or spec files. Note any `docs/` hits and fix them in Task 9.

What this sweep actually found, recorded here because it changed later tasks:
`docker-publish-code-interpreter.yml:80` builds from `./Dockerfile.streamlit` — a
copy-paste error from 2026-07-04 that has been publishing the Streamlit image
under the code-interpreter name. Task 8 Step 4 repoints it. And
`docker-compose.override.yml` is gitignored, so it is not tracked and never
appears in a fresh checkout.

- [ ] **Step 5: Commit**

```bash
rtk git add Makefile
rtk git commit -m "$(cat <<'EOF'
build(docker): drop per-image Dockerfiles for shared targets

Dockerfile.api, .streamlit and .combined are superseded by the single
multi-stage Dockerfile. Dockerfile.code-interpreter is unchanged.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Fix the compose healthchecks and build targets

`docker-compose.yml` declares its own `healthcheck.test`, which **overrides** the image's. Both entries call `curl`, which is not installed, so compose-run containers report unhealthy regardless of what the Dockerfile does.

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.api.yml`
- Modify: `docker-compose.streamlit.yml`

**Interfaces:**
- Consumes: `/health` (Task 1), `/_stcore/health` (Task 4), the `api` and `streamlit` targets (Tasks 3 and 4).
- Produces: a compose stack whose services reach `healthy`.

**Scope correction.** The original plan named `docker-compose.override.yml` here. That
file is gitignored, so it is not tracked and does not exist in a fresh checkout —
nothing to change. Meanwhile two tracked compose files it never mentioned,
`docker-compose.api.yml` and `docker-compose.streamlit.yml`, both name the
Dockerfiles Task 6 deleted and both carry the same broken `curl` healthcheck.
They are in scope because Task 6's deletion is what broke them.

`docker-compose.combined.yml` needs no change: it pulls a published image and
declares no `build` stanza and no healthcheck, so it inherits the image's own.

- [ ] **Step 1: Replace the api service healthcheck in `docker-compose.yml`**

```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status == 200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
```

- [ ] **Step 2: Replace the streamlit service healthcheck in `docker-compose.yml`**

```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5).status == 200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

- [ ] **Step 3: Repair `docker-compose.api.yml`**

Its `build` stanza names the deleted `Dockerfile.api`, and its healthcheck calls
`curl`. Change the `build` block and the `healthcheck` block only — leave the
volumes, ports, environment, networks and volumes sections untouched:

```yaml
    build:
      context: .
      dockerfile: Dockerfile
      target: api
```

```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status == 200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
```

- [ ] **Step 3b: Repair `docker-compose.streamlit.yml`**

Same two blocks. Note this file's healthcheck additionally uses the legacy
`/healthz` path, which must become `/_stcore/health`:

```yaml
    build:
      context: .
      dockerfile: Dockerfile
      target: streamlit
```

```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5).status == 200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

- [ ] **Step 4: Verify the stack comes up healthy**

```bash
docker compose up --build -d
sleep 60
docker compose ps
docker compose down
```

Expected: both services show `(healthy)` in the `STATUS` column.

If a service is healthy but its logs show permission errors writing to `/app/output`, that is the pre-existing host-UID mismatch on the bind mounts noted in the spec, not a regression from this work. Record it; do not fix it here.

- [ ] **Step 5: Confirm no compose file still names a deleted Dockerfile**

```bash
rtk grep -n "Dockerfile\.\(api\|streamlit\|combined\)" docker-compose*.yml || echo "NO_STALE_REFS"
```

Expected: `NO_STALE_REFS`. Any hit is a file this task missed.

- [ ] **Step 6: Commit**

```bash
rtk git add docker-compose.yml docker-compose.api.yml docker-compose.streamlit.yml
rtk git commit -m "$(cat <<'EOF'
fix(docker): repair compose healthchecks

Compose healthcheck.test overrides the image's, and both entries called
curl, which the slim base does not install — so compose services could
never report healthy. Use the interpreter, and the current Streamlit
health path.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Retarget the CI publish workflows

**Files:**
- Modify: `.github/workflows/docker-publish-api.yml:80,83,84`
- Modify: `.github/workflows/docker-publish-streamlit.yml` (same three lines)
- Modify: `.github/workflows/docker-publish-combined.yml` (same three lines)
- Modify: `.github/workflows/docker-publish-code-interpreter.yml:80` (one line; see Step 4)

**Interfaces:**
- Consumes: the `api`, `streamlit`, `combined` targets.
- Produces: three workflows building from one Dockerfile against one shared cache scope.

- [ ] **Step 1: Edit `docker-publish-api.yml`**

In the `Build and push by digest` step, replace the `file` line and both cache lines:

```yaml
          file: ./Dockerfile
          target: api
          platforms: ${{ matrix.platform }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha,scope=epic-news-${{ env.PLATFORM_PAIR }}
          cache-to: type=gha,mode=max,scope=epic-news-${{ env.PLATFORM_PAIR }}
```

Leave `context`, `outputs`, and every other step untouched.

- [ ] **Step 2: Edit `docker-publish-streamlit.yml`**

Identical change, with `target: streamlit`:

```yaml
          file: ./Dockerfile
          target: streamlit
          platforms: ${{ matrix.platform }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha,scope=epic-news-${{ env.PLATFORM_PAIR }}
          cache-to: type=gha,mode=max,scope=epic-news-${{ env.PLATFORM_PAIR }}
```

- [ ] **Step 3: Edit `docker-publish-combined.yml`**

Identical change, with `target: combined`:

```yaml
          file: ./Dockerfile
          target: combined
          platforms: ${{ matrix.platform }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha,scope=epic-news-${{ env.PLATFORM_PAIR }}
          cache-to: type=gha,mode=max,scope=epic-news-${{ env.PLATFORM_PAIR }}
```

The three images share one scope deliberately: their `builder` stage is byte-identical, so one cached dependency install serves all three. The workflows are triggered by the same push and run concurrently, so they still all miss on a cold run — the benefit lands on subsequent runs. Concurrent `mode=max` writers to one scope produce a benign conflict warning from the later writers because cache keys are immutable once created; the first writer's layers remain available to everyone.

- [ ] **Step 4: Repair `docker-publish-code-interpreter.yml`**

This workflow is otherwise out of scope, but Task 6 broke it: line 80 reads
`file: ./Dockerfile.streamlit`, a copy-paste error dating from 2026-07-04 that
has been publishing the Streamlit image under the `epic-news-code-interpreter`
name. That Dockerfile no longer exists, so the workflow now hard-fails.

By human decision, repoint it at the file it always meant:

```yaml
          file: ./Dockerfile.code-interpreter
```

Change that one line. Do **not** add a `target:` — `Dockerfile.code-interpreter`
is a single-stage file. Do not touch this workflow's cache scope: it keeps its
own `${{ env.IMAGE_NAME }}-${{ env.PLATFORM_PAIR }}` scope, because its builder
stage shares nothing with the other three.

Note for the PR description: the next publish changes that image's contents from
Streamlit to an actual code interpreter.

- [ ] **Step 5: Validate the YAML**

Run: `uv run yamllint -s .github/workflows/docker-publish-api.yml .github/workflows/docker-publish-streamlit.yml .github/workflows/docker-publish-combined.yml .github/workflows/docker-publish-code-interpreter.yml`

Expected: no errors.

Then confirm the change set is exactly the four intended workflows:

```bash
rtk git diff --name-only .github/workflows/
```

Expected: four files — the three retargeted publishers plus
`docker-publish-code-interpreter.yml`. Nothing else under `.github/`.

- [ ] **Step 6: Commit**

```bash
rtk git add .github/workflows/docker-publish-api.yml .github/workflows/docker-publish-streamlit.yml .github/workflows/docker-publish-combined.yml .github/workflows/docker-publish-code-interpreter.yml
rtk git commit -m "$(cat <<'EOF'
ci(docker): build from shared Dockerfile targets

All three images now build from one Dockerfile via --target, against a
single GHA cache scope, so the identical builder stage is installed once
and reused across images run to run.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Full verification sweep and PR

**Files:**
- Modify: any `docs/` file found referencing a deleted Dockerfile in Task 6 Step 4.

**Interfaces:**
- Consumes: everything above.
- Produces: recorded evidence for each of the three drivers, and a PR.

- [ ] **Step 1: Run the test suite**

Run: `uv run pytest -q`

Expected: green. If pytest is missing, `uv sync --all-extras` first — a plain `uv sync` prunes the test extras.

- [ ] **Step 2: Run lint and type checks**

Run: `make fix && uv run ruff check . && uv run mypy src/epic_news`

Expected: clean. If the mypy pre-commit hook later hangs past five minutes, its cache is cold — warm `.mypy_cache` in the background rather than bypassing the hook.

- [ ] **Step 3: Record the security evidence for all three images**

```bash
for img in api streamlit combined; do
  echo "=== $img ==="
  docker run --rm epic_news-$img:latest sh -c 'for b in git uv uvx; do command -v "$b" && echo "FAIL_PRESENT $b"; done; echo CHECK_DONE'
  docker run --rm epic_news-$img:latest sh -c "python -c 'import mypy' 2>&1 | tail -1"
  docker run --rm epic_news-$img:latest sh -c "python -c 'import pytest' 2>&1 | tail -1"
  echo -n "uid: "; docker run --rm epic_news-$img:latest id -u
done
```

Expected for each: `CHECK_DONE` with no preceding `FAIL_PRESENT`, two
`ModuleNotFoundError` lines, and a non-zero uid — including `combined`.

The loop is not a stylistic choice. `command -v git uv uvx` evaluates only
`git`, so it prints nothing, the `||` branch fires, and `uv`/`uvx` are never
looked at — which is exactly how they shipped undetected. Before trusting any
rewrite of this check, run it against an image known to still contain `uv` and
confirm it reports the failure.

- [ ] **Step 4: Record the rebuild-time evidence**

```bash
docker build --target api -t epic_news-api:latest . >/dev/null
touch src/epic_news/api.py
time docker build --target api --progress=plain -t epic_news-api:latest . 2>&1 | grep -E "uv sync --locked --no-install-project" -A2
```

Expected: the dependency step reports `CACHED`. Record the elapsed time.

- [ ] **Step 5: Record sizes for the record only**

```bash
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep epic_news
```

Size is not a success criterion. Record the numbers without editorialising.

- [ ] **Step 6: Fix any stale documentation references**

Using the `docs/` hits from Task 6 Step 4, update any prose naming `Dockerfile.api`, `Dockerfile.streamlit` or `Dockerfile.combined` to the new `--target` form. If there are none, skip this step and say so.

- [ ] **Step 7: Commit any documentation fixes**

```bash
# Only if step 6 changed files. Stage them explicitly by path.
rtk git add docs/<changed-file>
rtk git commit -m "$(cat <<'EOF'
docs: point Docker instructions at the shared Dockerfile targets

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 8: Open the PR**

Never commit `src/epic_news/main.py` — verify it is not staged before pushing.

```bash
rtk git status --short
rtk git checkout -b build/docker-multistage-restructure 2>/dev/null || rtk git branch --show-current
rtk git push -u origin HEAD
```

Then open a PR whose body records, under a `## Verification` heading, the evidence gathered in steps 3 to 5 plus the context-size before and after from Task 2, the healthy statuses from Tasks 3 to 5 and 7, and the WeasyPrint `PDF_OK` result from Task 3 Step 6.

- [ ] **Step 9: Wait for CI and review before merging**

Check CodeRabbitAI comments and every CI check. A red check blocks the merge even if it was already failing on `main` — fix it in this PR. The three Docker publish workflows run on pull requests with `push=false`, so this PR exercises the new build path end to end before anything is published.

---

## Out of scope, recorded for later

From the spec's deferred list. Do not implement any of these here:

- Split `pyproject.toml` into `[api]` / `[ui]` extras so the api image drops streamlit, pyarrow and pydeck.
- Investigate excluding the CrewAI memory/RAG stack (lancedb, onnxruntime, chromadb, kubernetes) — risky, since a CrewAI `Flow` always attaches a default `Memory`.
- Replace `pypandoc-binary` with `pypandoc` plus an apt `pandoc`.
- Drop `pymupdf`, which nothing under `src/` imports.
- Modernise or delete `Dockerfile.code-interpreter`.
