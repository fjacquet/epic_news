# Epic News Docker Deployment Guide

This guide outlines the best practices and key lessons learned for building and running Docker containers for the Epic News project, with a focus on using `uv` for dependency management.

## Key Principles for `uv` in Docker

Based on the official `uv` documentation and our experience, the following principles should be applied to create efficient, secure, and reliable Docker images.

1.  **Use Official `uv` Base Images**: Start with `ghcr.io/astral-sh/uv:python3.11-bookworm-slim` instead of a generic Python image.
2.  **Use `uv sync --locked`**: This is the fastest and most reliable way to install dependencies from a `uv.lock` file.
3.  **Leverage Docker Layer Caching**: Install system and Python dependencies *before* copying your application source code to avoid reinstalling them on every code change.
4.  **Run as a Non-Root User**: Always create and switch to a non-root user for security.
5.  **Use `uv run`**: Execute commands like `uvicorn` with `uv run` to ensure they run within the correct virtual environment.

## Final `Dockerfile.api` Example

Here is the final, optimized `Dockerfile.api` that incorporates all these lessons:

```dockerfile
# 1. Use the official uv image for Python 3.11
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# 2. Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Set the working directory
WORKDIR /app

# 4. Install system dependencies required by WeasyPrint
# Note: libpangoft2-1.0-0 was a critical missing dependency.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy dependency definitions
COPY pyproject.toml uv.lock ./

# 6. Install dependencies into a virtual environment using uv
RUN uv sync --locked

# 7. Copy the application source code
# We copy the contents of 'src/' into the WORKDIR to make 'epic_news' a top-level package.
COPY src/ .

# 8. Create and switch to a non-root user for security
RUN useradd -m myuser && chown -R myuser:myuser /app
USER myuser

# 9. Expose the port the app runs on
EXPOSE 8000

# 10. Healthcheck to verify the API is responsive
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD uv run curl -f http://localhost:8000/health || exit 1

# 11. Command to run the application
CMD ["uv", "run", "uvicorn", "epic_news.api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```

## Troubleshooting and Lessons Learned

### Python Import Errors

-   **`ModuleNotFoundError: No module named 'epic_news'`**: This error occurs when the `uvicorn` command can't find the application. It was solved by copying the source code via `COPY src/ .` and using `epic_news.api:app` as the application target.
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
