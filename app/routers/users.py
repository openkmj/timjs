"""
User API endpoints
"""

from fastapi import APIRouter

from app.db import query
from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import UpdatePushTokenRequest, UserMeResponse

router = APIRouter()


@router.get("/me", response_model=UserMeResponse)
async def get_me(_: DBContext, user: AuthContext):
    """
    Get current user's profile
    """
    return user


@router.put("/push-token")
async def update_push_token(
    db: DBContext, user: AuthContext, request: UpdatePushTokenRequest
):
    """
    Update user's expo push token
    """
    query.update_user_push_token(db, user.id, request.expo_push_token)
    return {"message": "Push token updated successfully"}
