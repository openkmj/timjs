"""
Media API endpoints
"""

from fastapi import APIRouter

from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import (
    ConfirmUploadRequest,
    MediaFeedResponse,
    MediaResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
)

router = APIRouter()


@router.post("/presigned-url", response_model=PresignedUploadResponse)
async def get_presigned_upload_url(user: AuthContext, request: PresignedUploadRequest):
    """
    Get a presigned URL for direct upload to S3
    """


@router.post("", response_model=MediaResponse)
async def create_media(db: DBContext, user: AuthContext, request: ConfirmUploadRequest):
    pass


@router.get("", response_model=MediaFeedResponse)
async def get_media_feed(db: DBContext, user: AuthContext):
    pass


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media_detail(db: DBContext, user: AuthContext, media_id: int):
    """
    Get media detail by ID
    """
    pass


@router.delete("/{media_id}")
async def delete_media(db: DBContext, user: AuthContext, media_id: int):
    """
    Delete media (only uploader can delete)
    """
    pass
