from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import query
from app.db.models import User
from app.middlewares.db import DBContext

security = HTTPBearer()
Credentials = Annotated[HTTPAuthorizationCredentials, Depends(security)]


async def _get_current_user(credentials: Credentials, db: DBContext) -> User:
    token = credentials.credentials

    if not token:
        raise HTTPException(status_code=401, detail="API key is required")

    user = query.get_user_by_api_key(db, token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user


AuthContext = Annotated[User, Depends(_get_current_user)]
