"""
Database queries for events and media
"""

import math
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Event, Media, Team, User


def list_events(db: Session, team_id: int) -> list[Event]:
    events = (
        db.query(Event)
        .filter(Event.team_id == team_id)
        .order_by(Event.date.desc())
        .all()
    )

    # Preload thumbnails for all events (max 3 per event)
    if events:
        event_ids = [e.id for e in events]
        # Get up to 3 media items per event, ordered by creation date

        # Subquery to get row numbers for each event's media
        subq = (
            select(
                Media.id,
                Media.event_id,
                Media.thumb_url,
                func.row_number()
                .over(
                    partition_by=Media.event_id,
                    order_by=Media.created_at.desc()
                )
                .label("rn")
            )
            .where(Media.event_id.in_(event_ids))
        ).subquery()

        # Get only the first 3 media items per event
        thumbnails = (
            db.query(
                subq.c.event_id,
                subq.c.thumb_url
            )
            .filter(subq.c.rn <= 3)
            .all()
        )

        # Group thumbnails by event_id
        thumbnails_by_event = {}
        for event_id, thumb_url in thumbnails:
            if event_id not in thumbnails_by_event:
                thumbnails_by_event[event_id] = []
            thumbnails_by_event[event_id].append(thumb_url)

        # Attach thumbnails to events
        for event in events:
            event.thumbnails = thumbnails_by_event.get(event.id, [])

    return events


def get_event(db: Session, event_id: int, team_id: int) -> Event | None:
    return (
        db.query(Event).filter(Event.id == event_id, Event.team_id == team_id).first()
    )


def create_event(
    db: Session,
    title: str,
    date: datetime,
    team_id: int,
    description: str | None = None,
    location: str | None = None,
    tags: list[str] | None = None,
):
    """Create a new event"""
    tags_str = ",".join(tags) if tags else None

    event = Event(
        title=title,
        description=description,
        date=date,
        location=location,
        tags=tags_str,
        team_id=team_id,
    )
    db.add(event)
    db.commit()


def update_event(
    db: Session,
    event: Event,
    title: str | None = None,
    date: datetime | None = None,
    description: str | None = None,
    location: str | None = None,
    tags: list[str] | None = None,
):
    """Update an event"""
    if title is not None:
        event.title = title
    if date is not None:
        event.date = date
    if description is not None:
        event.description = description
    if location is not None:
        event.location = location
    if tags is not None:
        event.tags = ",".join(tags) if tags else None

    db.commit()


def delete_event(db: Session, event: Event) -> None:
    """Delete an event (only if no media is connected)"""
    db.delete(event)
    db.commit()


def has_media(db: Session, event_id: int) -> bool:
    """Check if event has any media"""
    return db.query(Media).filter(Media.event_id == event_id).count() > 0


# Media queries


def get_media(db: Session, media_id: int) -> Media | None:
    """Get media by ID"""
    return db.query(Media).filter(Media.id == media_id).first()


def create_media_bulk(
    db: Session,
    user_id: int,
    media_data_list: list[dict],
    team_id: int,
) -> list[Media]:
    media_objects = [
        Media(
            event_id=data["event_id"],
            user_id=user_id,
            url=data["url"],
            thumb_url=data["thumb_url"],
            file_type=data["file_type"],
            file_size=data["file_size"],
            file_metadata=data.get("file_metadata"),
            created_at=data["created_at"],
        )
        for data in media_data_list
    ]

    db.add_all(media_objects)

    # Calculate total size in KB from media_data_list
    total_bytes = sum(data["file_size"] for data in media_data_list)
    size_kb = math.ceil(total_bytes / 1024)

    team = db.query(Team).filter(Team.id == team_id).first()
    team.storage_used += size_kb

    db.commit()


def delete_media(db: Session, media: Media, team_id: int) -> None:
    # Calculate size in KB before deleting
    size_kb = math.ceil(media.file_size / 1024) if media.file_size else 0

    db.delete(media)

    team = db.query(Team).filter(Team.id == team_id).first()
    team.storage_used -= size_kb
    if team.storage_used < 0:
        team.storage_used = 0

    db.commit()


def get_media_feed(
    db: Session, limit: int = 20, cursor: int | None = None, team_id: int | None = None
) -> tuple[list[Media], int | None, bool]:
    """
    Get media feed with pagination (with user join)
    Returns: (media_list, next_cursor, has_more)
    """
    query_obj = (
        db.query(Media)
        .join(Media.event)
        .options(joinedload(Media.user))
        .order_by(Media.created_at.desc(), Media.id.desc())
    )

    # Filter by team
    if team_id is not None:
        query_obj = query_obj.filter(Event.team_id == team_id)

    if cursor:
        cursor_media = db.query(Media).filter(Media.id == cursor).first()
        if cursor_media:
            query_obj = query_obj.filter(
                (Media.created_at < cursor_media.created_at)
                | (
                    (Media.created_at == cursor_media.created_at)
                    & (Media.id < cursor_media.id)
                )
            )

    media_list = query_obj.limit(limit + 1).all()

    has_more = len(media_list) > limit
    if has_more:
        media_list = media_list[:limit]

    next_cursor = media_list[-1].id if media_list and has_more else None

    return media_list, next_cursor, has_more


# User queries


def get_user(
    db: Session, api_key: str | None = None, user_id: int | None = None
) -> User | None:
    if api_key:
        return db.query(User).filter(User.api_key == api_key).first()
    if user_id:
        return db.query(User).filter(User.id == user_id).first()

    raise ValueError("Either api_key or user_id must be provided")


def list_users(db: Session, team_id: int) -> list[User]:
    return db.query(User).filter(User.team_id == team_id).all()


def update_user(
    db: Session,
    user_id: int,
    expo_push_token: str | None = None,
    profile_img: str | None = None,
) -> None:
    user = db.query(User).filter(User.id == user_id).first()

    if expo_push_token:
        user.expo_push_token = expo_push_token
    if profile_img:
        user.profile_img = profile_img
    db.commit()


# Team queries


def get_team(db: Session, team_id: int) -> Team:
    return db.query(Team).filter(Team.id == team_id).first()
