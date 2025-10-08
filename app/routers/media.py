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
    ConfirmUploadListRequest,
    MediaFeedResponse,
    MediaListItem,
    PresignedUploadRequest,
    PresignedUploadResponse,
    PresignedUrlData,
    UserSummary,
)
from app.utils.push_notification import send_push_notification
from app.utils.s3 import MediaType, s3_client

router = APIRouter()


@router.post("/presigned-url", response_model=PresignedUploadResponse)
async def get_presigned_upload_url(
    db: DBContext, user: AuthContext, request: PresignedUploadRequest
):
    """
    Get presigned URLs for direct upload to S3 (original and thumbnail)
    """
    event = query.get_event_by_id(db, request.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    original = s3_client.generate_presigned_post(
        file_name=request.file_name,
        content_type=request.content_type,
        event_s3_key=event.s3_key,
        media_type=MediaType.ORIGINAL,
    )

    thumbnail = s3_client.generate_presigned_post(
        file_name=request.file_name,
        content_type=request.content_type,
        event_s3_key=event.s3_key,
        media_type=MediaType.THUMBNAIL,
    )

    if not original or not thumbnail:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    return PresignedUploadResponse(
        original=PresignedUrlData(
            url=original["url"], fields=original["fields"], key=original["key"]
        ),
        thumbnail=PresignedUrlData(
            url=thumbnail["url"], fields=thumbnail["fields"], key=thumbnail["key"]
        ),
    )


@router.post("", status_code=204)
async def create_media(
    db: DBContext, user: AuthContext, request: ConfirmUploadListRequest
):
    """
    Confirm upload and create multiple media records
    """
    now = datetime.now()
    media_data_list = [
        {
            "event_id": media.event_id,
            "url": media.url,
            "thumb_url": media.thumb_url,
            "file_type": media.file_type,
            "file_size": media.file_size,
            "file_metadata": json.dumps(media.file_metadata)
            if media.file_metadata
            else None,
            "created_at": now,
        }
        for media in request.media_list
    ]

    query.create_media_bulk(db=db, user_id=user.id, media_data_list=media_data_list)

    # Send push notification once for all uploads
    users = query.list_users(db)
    tokens = [u.expo_push_token for u in users if u.expo_push_token and u.id != user.id]

    count = len(media_data_list)
    body = (
        f"{user.name}님이 사진 {count}개를 추가했습니다"
        if count > 1
        else f"{user.name}님이 사진을 추가했습니다"
    )

    send_push_notification(
        tokens=tokens,
        title="새로운 사진",
        body=body,
        data={"type": "new_media"},
    )


@router.get("", response_model=MediaFeedResponse)
async def get_media_feed(db: DBContext, user: AuthContext, cursor: int | None = None):
    """
    Get media feed with pagination
    """
    media_list, next_cursor, has_more = query.get_media_feed(
        db, limit=50, cursor=cursor
    )

    items = []
    for media in media_list:
        # Parse file_metadata safely
        metadata = None
        if media.file_metadata:
            try:
                metadata = json.loads(media.file_metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = None

        items.append(
            MediaListItem(
                id=media.id,
                event_id=media.event_id,
                user=UserSummary(id=media.user.id, name=media.user.name),
                url=media.url,
                thumb_url=media.thumb_url,
                file_type=media.file_type,
                file_size=media.file_size,
                file_metadata=metadata,
                created_at=media.created_at,
            )
        )

    return MediaFeedResponse(items=items, cursor=next_cursor, has_more=has_more)


@router.delete("/{media_id}", status_code=204)
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
