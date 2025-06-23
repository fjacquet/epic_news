from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

from epic_news.main import kickoff

app = FastAPI(
    title="Epic News API",
    description="API for triggering Epic News crews.",
    version="0.1.0",
)


class KickoffRequest(BaseModel):
    user_request: str


@app.post("/kickoff", status_code=202)
async def kickoff_endpoint(request: KickoffRequest, background_tasks: BackgroundTasks):
    """
    Triggers a crew to run in the background based on the user's request.

    This endpoint accepts a user request, adds the main `kickoff` function
    to a background task queue, and immediately returns a confirmation.
    This non-blocking approach is ideal for webhooks or other automated triggers.
    """
    background_tasks.add_task(kickoff, user_input=request.user_request)
    return {"message": "Crew kickoff initiated successfully.", "user_request": request.user_request}
