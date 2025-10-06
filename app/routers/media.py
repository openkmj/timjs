"""
Media API endpoints
"""

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.db import query
from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import (
    ConfirmUploadRequest,
    MediaFeedResponse,
    MediaResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
    UserSummary,
)
from app.utils.s3 import MediaType, s3_client

router = APIRouter()


@router.post("/presigned-url", response_model=PresignedUploadResponse)
async def get_presigned_upload_url(user: AuthContext, request: PresignedUploadRequest):
    """
    Get presigned URLs for direct upload to S3 (original and thumbnail)
    """
    original = s3_client.generate_presigned_post(
        file_name=request.file_name,
        content_type=request.content_type,
        event_id=request.event_id,
        media_type=MediaType.ORIGINAL,
    )

    thumbnail = s3_client.generate_presigned_post(
        file_name=request.file_name,
        content_type=request.content_type,
        event_id=request.event_id,
        media_type=MediaType.THUMBNAIL,
    )

    if not original or not thumbnail:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    from app.schemas import PresignedUrlData

    return PresignedUploadResponse(
        original=PresignedUrlData(
            url=original["url"], fields=original["fields"], key=original["key"]
        ),
        thumbnail=PresignedUrlData(
            url=thumbnail["url"], fields=thumbnail["fields"], key=thumbnail["key"]
        ),
    )


@router.post("", response_model=MediaResponse)
async def create_media(db: DBContext, user: AuthContext, request: ConfirmUploadRequest):
    """
    Confirm upload and create media record
    """
    media = query.create_media(
        db=db,
        user_id=user.id,
        event_id=request.event_id,
        url=request.url,
        thumb_url=request.thumb_url,
        file_type=request.file_type,
        file_size=request.file_size,
        created_at=datetime.now(),
        file_metadata=json.dumps(request.file_metadata) if request.file_metadata else None,
    )

    return MediaResponse(
        id=media.id,
        event_id=media.event_id,
        user=UserSummary(id=media.user.id, name=media.user.name),
        url=media.url,
        thumb_url=media.thumb_url,
        file_type=media.file_type,
        file_size=media.file_size,
        file_metadata=json.loads(media.file_metadata) if media.file_metadata else None,
        created_at=media.created_at,
    )


@router.get("", response_model=MediaFeedResponse)
async def get_media_feed(
    db: DBContext, user: AuthContext, cursor: int | None = None, limit: int = 20
):
    """
    Get media feed with pagination
    """
    media_list, next_cursor, has_more = query.get_media_feed(
        db, limit=limit, cursor=cursor
    )

    from app.schemas import MediaListItem

    items = [
        MediaListItem(
            id=media.id,
            event_id=media.event_id,
            url=media.url,
            thumb_url=media.thumb_url,
            file_type=media.file_type,
            created_at=media.created_at,
        )
        for media in media_list
    ]

    return MediaFeedResponse(
        items=items, cursor=str(next_cursor) if next_cursor else None, has_more=has_more
    )


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media_detail(db: DBContext, user: AuthContext, media_id: int):
    """
    Get media detail by ID
    """
    media = query.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    return MediaResponse(
        id=media.id,
        event_id=media.event_id,
        user=UserSummary(id=media.user.id, name=media.user.name),
        url=media.url,
        thumb_url=media.thumb_url,
        file_type=media.file_type,
        file_size=media.file_size,
        file_metadata=json.loads(media.file_metadata) if media.file_metadata else None,
        created_at=media.created_at,
    )


@router.delete("/{media_id}")
async def delete_media(db: DBContext, user: AuthContext, media_id: int):
    """
    Delete media (only uploader can delete)
    """
    media = query.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if media.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this media"
        )

    query.delete_media(db, media)
    return {"message": "Media deleted successfully"}
