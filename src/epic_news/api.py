import hmac
import os
import threading
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel, Field

from epic_news.main import kickoff

app = FastAPI(
    title="Epic News API",
    description="API for triggering Epic News crews.",
    version="0.1.0",
)

_bearer = HTTPBearer(auto_error=False)

# Caps how many crew kickoffs may run at once; the slot is released when the
# background run finishes (successfully or not).
_kickoff_slots = threading.BoundedSemaphore(max(1, int(os.getenv("EPIC_API_MAX_CONCURRENT", "1"))))


class KickoffRequest(BaseModel):
    user_request: str = Field(max_length=2000)


def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    """Check the bearer token against EPIC_API_TOKEN; fail closed if it is unset."""
    expected = os.getenv("EPIC_API_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API token not configured"
        )
    supplied = credentials.credentials if credentials else ""
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _run_kickoff(user_input: str) -> None:
    """Run the flow, then free the concurrency slot whatever happens."""
    try:
        kickoff(user_input=user_input)
    except Exception:
        logger.exception("Background kickoff failed")
    finally:
        _kickoff_slots.release()


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe for the container HEALTHCHECK and docker-compose.

    Deliberately does no dependency checking: it answers "is the ASGI app
    accepting requests", not "is every downstream provider reachable".
    """
    return {"status": "ok"}


@app.post("/kickoff", status_code=202, dependencies=[Depends(require_token)])
async def kickoff_endpoint(request: KickoffRequest, background_tasks: BackgroundTasks):
    """
    Triggers a crew to run in the background based on the user's request.

    This endpoint accepts a user request, adds the main `kickoff` function
    to a background task queue, and immediately returns a confirmation.
    This non-blocking approach is ideal for webhooks or other automated triggers.
    Requires `Authorization: Bearer <EPIC_API_TOKEN>`; returns 429 when the
    concurrency cap (EPIC_API_MAX_CONCURRENT) is reached.
    """
    if not _kickoff_slots.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="A kickoff is already running"
        )
    background_tasks.add_task(_run_kickoff, user_input=request.user_request)
    return {"message": "Crew kickoff initiated successfully.", "user_request": request.user_request}
