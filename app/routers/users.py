"""
User API endpoints
"""

from fastapi import APIRouter, HTTPException

from app.db import query
from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import (
    FriendSummary,
    PresignedUrlData,
    ProfileImagePresignedRequest,
    UpdateProfileImageRequest,
    UpdatePushTokenRequest,
    UserMeResponse,
)
from app.utils.s3 import MediaType, s3_client

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


@router.post("/profile-image/presigned-url", response_model=PresignedUrlData)
async def get_profile_image_presigned_url(
    user: AuthContext, request: ProfileImagePresignedRequest
):
    """
    Get presigned URL for profile image upload to S3
    """
    presigned_data = s3_client.generate_presigned_post(
        file_name=request.file_name,
        content_type=request.content_type,
        event_s3_key=str(user.id),
        media_type=MediaType.PROFILE,
    )

    if not presigned_data:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    return PresignedUrlData(
        url=presigned_data["url"],
        fields=presigned_data["fields"],
        key=presigned_data["key"],
    )


@router.put("/profile-image", status_code=204)
async def update_profile_image(
    db: DBContext, user: AuthContext, request: UpdateProfileImageRequest
):
    """
    Update user's profile image
    """
    query.update_user_profile_image(db, user.id, request.url)
