"""
Media API endpoints
"""

import json
import math
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.config import get_settings
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
    event = query.get_event(db, request.event_id, user.team_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    team = query.get_team(db, user.team_id)
    if team.storage_used >= team.storage_limit:
        raise HTTPException(
            status_code=403,
            detail="Storage limit exceeded.",
        )

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
    Fetches actual file metadata from S3 for validation
    """
    # Get current storage usage first
    team = query.get_team(db, user.team_id)
    storage_used, storage_limit = team.storage_used, team.storage_limit

    # Verify files, check storage, and build data list in one pass
    total_upload_size = 0
    media_data_list = []
    settings = get_settings()
    now = datetime.now()

    for media in request.media_list:
        metadata = s3_client.get_file_metadata(media.s3_key)

        if not metadata:
            raise HTTPException(
                status_code=400,
                detail=f"File not found in S3: {media.s3_key}",
            )

        total_upload_size += metadata["size"]
        upload_size_kb = math.ceil(total_upload_size / 1024)

        if storage_used + upload_size_kb > storage_limit:
            raise HTTPException(status_code=403, detail="Storage limit exceeded.")

        url = f"https://{settings.s3_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{media.s3_key}"
        thumb_url = f"https://{settings.s3_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{media.thumb_s3_key}"

        media_data_list.append(
            {
                "event_id": media.event_id,
                "url": url,
                "thumb_url": thumb_url,
                "file_type": metadata["content_type"],
                "file_size": metadata["size"],
                "file_metadata": json.dumps(media.file_metadata)
                if media.file_metadata
                else None,
                "created_at": now,
            }
        )

    query.create_media_bulk(
        db=db,
        user_id=user.id,
        media_data_list=media_data_list,
        team_id=user.team_id,
    )

    # Send push notification to team members
    users = query.list_users(db, user.team_id)
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
    media_list, next_cursor, has_more = query.get_media_feed(
        db, limit=50, cursor=cursor, team_id=user.team_id
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
    media = query.get_media(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    event = query.get_event(db, media.event_id, user.team_id)
    if event and event.team_id != user.team_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this media"
        )

    if media.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this media"
        )

    query.delete_media(db, media, user.team_id)
