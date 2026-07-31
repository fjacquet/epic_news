# Epic News Docker Deployment Guide

This guide covers building and running the Epic News containers, plus the
problems that have actually bitten us.

## The Dockerfile is the source of truth

There is one `Dockerfile` at the repository root. Read it — it is heavily
commented, and every comment records a failure that was paid for once already.
This guide does not reproduce it, because a copied example goes stale and then
teaches the opposite of what the real file does.

It is multi-stage. A `builder` stage resolves and installs the venv with `uv`
and is never shipped. A `runtime-base` stage starts from a plain
`python:3.13-slim-bookworm`, copies the finished venv and the source out of the
builder, and creates the writable data directories. Three targets build on it:

| Target | Serves | Port(s) | Use it for |
| --- | --- | --- | --- |
| `api` | FastAPI via `uvicorn` | 8000 | The API on its own; what most deployments want. |
| `streamlit` | The Streamlit UI | 8501 | The UI on its own, pointed at an external API via `API_URL`. |
| `combined` | Both, under `supervisord` | 8000, 8501 | A single-container deployment where running two is not worth it. |

`Dockerfile.code-interpreter` is separate and unrelated — it is the sandbox
image for the code-interpreter tool, not an application image.

## Building

```bash
docker build --target api       -t epic_news-api:latest       .
docker build --target streamlit -t epic_news-streamlit:latest .
docker build --target combined  -t epic_news-combined:latest  .
```

Or through the Makefile, which is the same commands with the project's tags:

```bash
make docker-build-api
make docker-build-streamlit
make docker-build-combined
make docker-build-all          # the three above plus code-interpreter
```

## Running

```bash
make docker-run-api            # publishes 8000
make docker-run-streamlit      # publishes 8501
make docker-run-combined       # publishes 8000 and 8501
```

Or with compose, which adds the bind mounts for `db/`, `data/`, `output/` and
`.env`:

```bash
docker compose -f docker-compose.api.yml up -d --build
docker compose -f docker-compose.streamlit.yml up -d --build
docker compose up -d           # api + streamlit from the published GHCR images
```

`docker-compose.api.yml` and `docker-compose.streamlit.yml` build locally from
the corresponding target. The root `docker-compose.yml` and
`docker-compose.combined.yml` pull the published `ghcr.io/fjacquet/epic-news-*`
images instead.

## Properties worth not breaking

These are deliberate, and each was a bug before it was a rule:

- **The container runs as `myuser`, and `/app`, `/app/src` and `/app/.venv` stay
  root-owned.** The COPY lines carry no `--chown`; `--chown` is recursive and
  would hand the runtime user write access to its own code and interpreter.
  Only the seven data directories (`db data output traces checkpoints debug
  logs`) are chowned. New write targets get added to that list, not fixed by
  widening ownership.
- **The venv and the source ship as one 1.52 GB layer, and splitting them does
  not help.** It was measured: `uv sync` reinstalls the project whenever the
  source changes and writes the source tree's byte size into the venv's
  `uv_cache.json`, so `COPY --from=builder /app/.venv` misses cache after any
  source edit anyway. Anyone attacking the rebuild cost needs a separate
  deps-only venv stage; a COPY split alone buys nothing.
- **Healthchecks call `python -c urllib.request`, not `curl`.** `curl` is not in
  the slim base; a healthcheck that shells out to a binary the image does not
  contain reports unhealthy forever. Nothing invokes `uv run` at runtime either
  — `uv` is deleted from the image.
- **No `VOLUME` declarations.** `VOLUME` makes Docker create a root-owned
  anonymous volume on every run, unwritable by `myuser` and leaked to disk.
  Compose bind-mounts host paths over those directories instead.
- **The build context is an allowlist.** `.dockerignore` excludes `*` and
  re-includes only what the build needs. A denylist once let a 234 MB
  `.mypy_cache` into every published image.

## Troubleshooting and Lessons Learned

### Python Import Errors

-   **`ModuleNotFoundError: No module named 'epic_news'`**: This error occurs when the `uvicorn` command can't find the application. `epic_news` resolves because the builder's second `uv sync --locked --no-dev` installs the project into the venv, which records `/app/src` in an editable `.pth` file. The application target is therefore `epic_news.api:app`, and `/app/src` must be copied to that exact path — a venv copied without its matching source tree imports nothing.
-   **`ModuleNotFoundError: No module named 'src'`**: This error was caused by incorrect absolute imports within the application code (e.g., `from src.epic_news...`). The fix was to remove the `src.` prefix from all imports, as `epic_news` is the top-level package inside the container, not `src`.

### WeasyPrint System Dependencies

-   **`ImportError: ... no library called "pangoft2-1.0" was found`**: WeasyPrint has several system dependencies that must be installed with `apt-get`. The key was to ensure the complete list was present, including the often-missed `libpangoft2-1.0-0`.

### Application Hangs at Startup

-   **Symptom**: The container starts, but the logs stop at a certain point and `uvicorn` never reports that it's running. In our case, the last log message was `Actions cache is outdated, refreshing cache...`.
-   **Cause**: A third-party library (`composio_crewai`) was performing a long-running, blocking operation as soon as it was imported. Because it was imported at the top level of a module, it blocked the entire application startup process.
-   **Solution (Lazy Loading)**: The import was moved from the top of the file into the specific method where the library was actually used. This defers the expensive import until it's needed, allowing the server to start without delay.

    **Before (Problem):**
    ```python
    from composio_crewai import ComposioToolSet # <-- This blocks at startup

    @CrewBase
    class CompanyNewsCrew:
        def __init__(self):
            self.toolset = ComposioToolSet()
            # ...
    ```

    **After (Solution):**
    ```python
    from crewai.project import CrewBase

    @CrewBase
    class CompanyNewsCrew:
        def __init__(self):
            from composio_crewai import ComposioToolSet # <-- Now imported only when needed

            self.toolset = ComposioToolSet()
            # ...
    ```

### Common Runtime Issues

1. **Database Errors**
   - Check file permissions on the db directory
2. **Missing Data Files**
   - Verify that the data directory contains the required feedly.opml file
3. **Environment Variables**
   - Confirm all required environment variables are set in the .env file

### Logs

To view container logs:

```bash
# API logs
docker-compose logs api

# Streamlit logs
docker-compose logs streamlit
```

## Maintenance

### Updating Images

Pull the latest images:

```bash
docker-compose pull
```

Restart services with new images:

```bash
docker-compose up -d
```

### Backup

Backup important data regularly:

```bash
# Backup database
cp -r ./db ./db_backup_$(date +%Y%m%d)

# Backup data
cp -r ./data ./data_backup_$(date +%Y%m%d)
```
