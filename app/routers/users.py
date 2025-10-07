"""
User API endpoints
"""

from fastapi import APIRouter

from app.db import query
from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import FriendSummary, UpdatePushTokenRequest, UserMeResponse

router = APIRouter()


@router.get("/me", response_model=UserMeResponse)
async def get_me(db: DBContext, user: AuthContext):
    """
    Get current user's profile with friends list
    """
    # Get all users except current user
    all_users = query.list_users(db)
    friends = [
        FriendSummary(id=u.id, name=u.name, profile_img=u.profile_img)
        for u in all_users
        if u.id != user.id
    ]

    return UserMeResponse(
        id=user.id,
        name=user.name,
        profile_img=user.profile_img,
        friends=friends,
    )


@router.put("/push-token", status_code=204)
async def update_push_token(
    db: DBContext, user: AuthContext, request: UpdatePushTokenRequest
):
    """
    Update user's expo push token
    """
    query.update_user_push_token(db, user.id, request.expo_push_token)
