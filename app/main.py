from fastapi import FastAPI

from app.routers import events, media

app = FastAPI(
    title="Backend API",
    description="Event and media management API",
    version="1.0.0",
)

app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(media.router, prefix="/api/media", tags=["media"])


@app.get("/")
async def root():
    return {"message": "OK"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
