from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from app.admin import AdminAuth, EventAdmin, MediaAdmin, TeamAdmin, UserAdmin
from app.config import get_settings
from app.db.connection import engine
from app.routers import events, media, users

app = FastAPI(
    title="Timjs Backend API",
    version="1.0.0",
)

app.add_middleware(SessionMiddleware, secret_key=get_settings().admin_secret_key)

app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    return {"message": "OK"}


# Admin setup
admin = Admin(
    app,
    engine=engine,
    base_url="/timjs/admin",
    authentication_backend=AdminAuth(secret_key=get_settings().admin_secret_key),
)
admin.add_view(TeamAdmin)
admin.add_view(UserAdmin)
admin.add_view(EventAdmin)
admin.add_view(MediaAdmin)
