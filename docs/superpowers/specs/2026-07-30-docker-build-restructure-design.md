# Docker Build Restructure — Design

**Date:** 2026-07-30
**Status:** Approved for planning

## Problem

The four Dockerfiles in this repo are single-stage, install development
dependencies into production images, ship a 233 MB mypy cache, invalidate the
dependency layer on every source edit, and declare healthchecks that can never
pass. Container images are rebuilt on every push to `main` across four images
and two architectures.

### Drivers

The user selected three drivers, in no particular order:

1. **Rebuild time** — a one-character source edit currently reinstalls every
   dependency.
2. **CI build minutes** — four images x two architectures per publish.
3. **Security / attack surface** — `git`, `uv`, dev tooling, and a stale mypy
   cache all reach production images.

**Image size on disk was explicitly _not_ selected as a driver.** This rules out
the expensive, higher-risk dependency work: no splitting `pyproject.toml` into
`[api]` / `[ui]` extras, no pruning the CrewAI memory/RAG stack
(lancedb + chromadb + onnxruntime + kubernetes, ~250 MB), no replacing
`pypandoc-binary` (114 MB) with an apt `pandoc`. Those remain available as
follow-up work if size ever becomes a driver. The 1.3 GB of wheels stays.

## Findings from exploration

Measured on the working tree at commit `573fd5a`.

| Finding | Evidence |
| --- | --- |
| 233 MB mypy cache ships in every image | `src/epic_news/crews/.mypy_cache/` is 234 MB; `.dockerignore` lists `.pytest_cache/` but not `.mypy_cache`; `COPY src/ ./src` bakes it in |
| Dev dependencies ship to production | `uv sync --locked` installs `[dependency-groups].dev` by default (mypy, ruff, pre-commit, bandit, deptry — mypy alone ~55 MB). No `--no-dev` in any Dockerfile |
| Test extras ship to production | `Dockerfile.streamlit` and `Dockerfile.combined` use `--all-extras`; the only extras group is `test` (pytest, faker, python-docx) |
| Dependency layer invalidated by source edits | `COPY src/ ./src` precedes `RUN uv sync` in all three in-scope Dockerfiles |
| No BuildKit features | No `# syntax` directive, no cache mounts, no bind mounts |
| Build tooling reaches runtime | Single-stage: `git` and the `uv` binary are present in the shipped image |
| Healthchecks can never pass | `curl` is not installed in the slim base. `Dockerfile.api:48` runs `uv run curl`; `Dockerfile.streamlit:50` runs `curl`; `docker-compose.yml` uses `CMD curl` for both services. Containers report `unhealthy` indefinitely |
| `VOLUME` declarations are harmful | `VOLUME /app/db`, `/app/data`, `/app/output` create root-owned anonymous volumes on each `docker run`, which the non-root `myuser` cannot write to |
| supervisord runs as root | `Dockerfile.combined` deliberately does not `USER myuser`; supervisord setuids each program |
| No bytecode anywhere | `PYTHONDONTWRITEBYTECODE=1` with no build-time compilation means every import compiles at each container start |

Confirmed still needed, so **not** removed:

- WeasyPrint apt libraries (`libpango-1.0-0`, `libpangoft2-1.0-0`,
  `libharfbuzz0b`, `libgdk-pixbuf-2.0-0`, `shared-mime-info`) —
  `src/epic_news/tools/html_to_pdf_tool.py` imports `weasyprint`.
- `git` in the **builder only** — `crewai-custom-tools` is a `git+https`
  dependency in `pyproject.toml`.
- `pypandoc-binary` — pandoc ships inside the wheel
  (`.venv/lib/python3.13/site-packages/pypandoc/files/pandoc`), so no apt
  `pandoc` package is required.

## Scope

**In scope:** the `api`, `streamlit`, and `combined` images, plus the shared
`.dockerignore`, `supervisord.conf`, `docker-compose.yml`, the three
corresponding CI publish workflows, and the Makefile docker targets.

**Out of scope:** `Dockerfile.code-interpreter` and
`docker-publish-code-interpreter.yml` are left untouched by explicit decision,
despite being stale (Python 3.12 against a project requiring 3.13, `uv sync`
with no lockfile, ships `build-essential`).

## Design

### 1. Build topology

A single `Dockerfile` at the repo root replaces `Dockerfile.api`,
`Dockerfile.streamlit`, and `Dockerfile.combined`, which are deleted.

```
builder ──> runtime-base ──┬──> api        (8000)
                           ├──> streamlit  (8501)
                           └──> combined   (8000 + 8501, + supervisor)
```

**`builder` stage**

- Base: `python:3.13-slim-bookworm`.
- `uv` obtained via `COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/`.
  Pinned to the minor version, matching the locally installed uv 0.12.0.
- Installs `git` (for the `git+https` dependency), then clears apt lists.
- `ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0`.
- Two-step sync:
  1. `RUN --mount=type=cache,target=/root/.cache/uv --mount=type=bind,source=uv.lock,target=uv.lock --mount=type=bind,source=pyproject.toml,target=pyproject.toml uv sync --locked --no-install-project --no-dev`
  2. `COPY src/ ./src` and `COPY templates/ ./templates`, then
     `RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev`

  Step 1 is invalidated only by a lockfile or manifest change. Step 2 installs
  just the project into the existing venv.

**`runtime-base` stage**

- Base: `python:3.13-slim-bookworm` — deliberately the **same** image as the
  builder, so the venv's interpreter symlinks resolve at the same path. This
  is why the builder does not use `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
  as its base; copying the `uv` binary into the official image keeps both stages
  on one interpreter and preserves the property the existing Dockerfile comments
  were protecting.
- Installs the five WeasyPrint apt libraries only. No `git`, no `uv`, no build
  tooling.
- Creates `myuser`, then — **in this order** — copies `/app` from the builder
  with `--chown=myuser:myuser`, and only afterwards runs
  `mkdir -p /app/db /app/data /app/output && chown myuser:myuser` on them. The
  order matters: a `COPY` into an existing `/app` merges rather than replaces,
  so creating the data directories first would leave their ownership
  unpredictable.
- `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app PATH=/app/.venv/bin:$PATH`.

  `UV_COMPILE_BYTECODE=1` at build time and `PYTHONDONTWRITEBYTECODE=1` at
  runtime are complementary, not contradictory: `.pyc` files are generated
  during the build, so the runtime never needs to write any. This also means
  the non-root user requires no write access to site-packages.

**Target stages**

Each target is `FROM runtime-base`, declares its `EXPOSE` and `HEALTHCHECK`,
sets `USER myuser`, and sets its `CMD` to a venv binary on `PATH` — `uvicorn`,
`streamlit`, or `/usr/bin/supervisord`.

`combined` additionally installs the `supervisor` apt package and copies
`supervisord.conf` **before** its `USER myuser` line, since apt requires root.
`USER myuser` is the last instruction before `CMD` in every target.

### 2. Dependency flags

- `--no-dev` on both sync steps in the builder, for all three targets.
- `--all-extras` is dropped. The only extras group is `test`; no target needs it.

### 3. Context hygiene — allowlist

`.dockerignore` is inverted from a denylist to an allowlist. The 233 MB mypy
cache entered the images because a denylist requires someone to remember every
new junk directory; the same hole would admit a `.env` variant.

```
*
!pyproject.toml
!uv.lock
!src/
!templates/
!supervisord.conf
src/**/__pycache__/
src/**/.mypy_cache/
src/**/.pytest_cache/
src/**/*.egg-info/
```

The trailing re-exclusions handle junk nested inside the allowed `src/` tree.
Anything new at the repo root is excluded by default.

### 4. Runtime hardening

**Healthchecks.** Replace every `curl` invocation with the venv interpreter:

```
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status == 200 else 1)"
```

This must be changed in **both** the Dockerfile targets and in
`docker-compose.yml`, whose `healthcheck.test` entries override the image's and
are equally broken today.

The Streamlit health endpoint must be confirmed against current Streamlit
documentation via context7 at implementation time before the value is written:
`/healthz` is the legacy path and `/_stcore/health` is the modern one. Do not
write either into the Dockerfile from memory.

**`VOLUME` removal.** All `VOLUME` lines are deleted from every target. The
directories are instead created at build time and chowned to `myuser`.
`docker-compose.yml` already bind-mounts host paths over them.

Note a pre-existing, separate concern this does not fix: the compose bind mounts
are owned by the host user, whose UID will not match `myuser`'s UID inside the
container. If writes to `./output` fail after this change, that UID mismatch is
the cause, not the `VOLUME` removal. It is called out here so it is not
misdiagnosed as a regression.

**De-rooting supervisord.** `combined` sets `USER myuser` like the other
targets. `supervisord.conf` changes:

- `[supervisord]` gains `pidfile=/tmp/supervisord.pid` and `logfile=/dev/null`
  (log output already goes to stdout/stderr per program).
- A `[unix_http_server] file=/tmp/supervisor.sock` section, so no write to
  `/var/run` is needed.
- `user=myuser` is removed from each `[program:*]` block — supervisord no longer
  runs as root, so it cannot and need not setuid.
- Both `command=` lines change from `uv run --no-cache <bin> ...` to the
  absolute venv path `/app/.venv/bin/<bin> ...`, since `uv` does not exist in
  the runtime image.

### 5. CI and Makefile wiring

The three publish workflows (`docker-publish-api.yml`,
`docker-publish-streamlit.yml`, `docker-publish-combined.yml`) each change:

- `file: Dockerfile.<name>` → `file: Dockerfile` plus `target: <name>`.
- `cache-from` / `cache-to` scope from `${{ env.IMAGE_NAME }}-${{ env.PLATFORM_PAIR }}`
  to a shared `epic-news-${{ env.PLATFORM_PAIR }}`.

Because the builder stage is byte-identical across the three images, a shared
scope lets all three reuse one cached dependency install. The three workflows
are triggered by the same push and run in parallel, so all three still miss on a
cold run; the benefit accrues on every subsequent run. Concurrent `mode=max`
writes to one scope cause the later writers to log a benign conflict — GitHub
cache keys are immutable once created — while the layers from the first writer
remain available to all.

`docker-publish-code-interpreter.yml` is untouched and keeps its own scope.

Makefile targets `docker-build-api`, `docker-build-streamlit`, and
`docker-build-combined` change from `-f Dockerfile.<name>` to
`-f Dockerfile --target <name>`. `docker-build-code-interpreter` is untouched.

## Verification

Every driver gets evidence, not an assertion. Measurements are recorded as
observed; no target number is promised.

**Rebuild time.** Build all three targets cold. Then `touch
src/epic_news/main.py` and rebuild. The `uv sync --no-install-project` layer
must report `CACHED` in `--progress=plain` output. Record both wall-clock times.

**Security.** For each of the three images:

- `docker run --rm <img> sh -c "command -v git uv"` returns empty.
- `docker run --rm <img> python -c "import mypy"` fails with `ModuleNotFoundError`.
- `docker run --rm <img> python -c "import pytest"` fails likewise.
- `docker run --rm <img> id -u` returns a non-zero UID — including `combined`.

**CI minutes.** Capture the `transferring context` byte count from the first
line of `docker build --no-cache --progress=plain` output, before and after.
Expected: roughly 350 MB down to under 2 MB.

**Not broken.** This is the gate that matters most, since the restructure
touches entrypoints:

- `api`: `/health` returns 200.
- `streamlit`: the health endpoint returns 200 and the app page loads.
- `combined`: both ports serve, and `supervisorctl status` shows both programs
  `RUNNING` under a non-root user.
- `docker inspect --format '{{.State.Health.Status}}'` reaches `healthy` for
  each image — this has never been true in this repo and is the proof the
  healthcheck fix works.
- One PDF render is exercised end to end through `html_to_pdf_tool`, proving
  the reduced apt list still satisfies WeasyPrint.

**Sizes.** `docker images` output recorded before and after for the record only.
Size is not a success criterion for this work.

## Deliverables

1. `Dockerfile` (new, three targets).
2. `Dockerfile.api`, `Dockerfile.streamlit`, `Dockerfile.combined` deleted.
3. `.dockerignore` rewritten as an allowlist.
4. `supervisord.conf` updated for non-root operation and venv paths.
5. `docker-compose.yml` healthchecks fixed.
6. Three CI publish workflows retargeted with a shared cache scope.
7. Three Makefile docker-build targets retargeted.
8. Verification results recorded in the PR description.

## Explicitly deferred

Available if image size later becomes a driver:

- Split `pyproject.toml` into `[api]` / `[ui]` extras so the api image drops
  streamlit + pyarrow + pydeck (~170 MB).
- Investigate excluding the CrewAI memory/RAG stack (lancedb 97 MB,
  onnxruntime 70 MB, chromadb_rust_bindings 45 MB, kubernetes 41 MB). Risky:
  see the known behaviour that a CrewAI `Flow` always attaches a default
  `Memory`, so these may be required at import time even though the project
  never uses RAG.
- Replace `pypandoc-binary` (114 MB) with `pypandoc` plus an apt `pandoc`.
- Drop `pymupdf` (52 MB) — nothing in `src/` imports it; it arrives via
  `crewai-tools`.
- Modernise or delete `Dockerfile.code-interpreter`.
