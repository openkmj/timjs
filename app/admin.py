from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.config import get_settings
from app.db.models import Event, Media, Team, User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        settings = get_settings()

        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({"authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("authenticated", False)


class TeamAdmin(ModelView, model=Team):
    column_list = [Team.id, Team.name, Team.storage_limit, Team.storage_used]


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.team_id,
        User.name,
        User.api_key,
        User.expo_push_token,
    ]


class EventAdmin(ModelView, model=Event):
    column_list = [Event.id, Event.team_id, Event.title]


class MediaAdmin(ModelView, model=Media):
    column_list = [
        Media.id,
        Media.event_id,
        Media.user_id,
        Media.url,
        Media.file_size,
        Media.created_at,
    ]
