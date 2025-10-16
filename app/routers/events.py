from fastapi import APIRouter, HTTPException

from app.db import query
from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import EventCreate, EventResponse, EventUpdate
from app.utils.push_notification import send_push_notification

router = APIRouter()


@router.get("", response_model=list[EventResponse])
async def get_events(db: DBContext, user: AuthContext):
    events = query.list_events(db, user.team_id)
    return [
        EventResponse(
            id=e.id,
            title=e.title,
            description=e.description,
            date=e.date,
            location=e.location,
            tags=e.tags.split(",") if e.tags else [],
        )
        for e in events
    ]


@router.post("", status_code=204)
async def create_event(db: DBContext, user: AuthContext, event: EventCreate):
    """
    Create a new event
    """
    query.create_event(
        db=db,
        title=event.title,
        date=event.date,
        team_id=user.team_id,
        description=event.description,
        location=event.location,
        tags=event.tags,
    )

    # Send push notifications to team members except the creator
    users = query.list_users(db, user.team_id)
    tokens = [u.expo_push_token for u in users if u.expo_push_token and u.id != user.id]
    send_push_notification(
        tokens=tokens,
        title=event.title,
        body=f"{user.name}님이 {event.title} 이벤트를 추가했습니다.",
        data={"type": "new_event"},
    )


@router.put("/{event_id}", status_code=204)
async def update_event(
    db: DBContext, user: AuthContext, event_id: int, event_update: EventUpdate
):
    """
    Update Event
    """
    event = query.get_event(db, event_id, user.team_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    query.update_event(
        db=db,
        event=event,
        title=event_update.title,
        date=event_update.date,
        description=event_update.description,
        location=event_update.location,
        tags=event_update.tags,
    )


@router.delete("/{event_id}", status_code=204)
async def delete_event(db: DBContext, user: AuthContext, event_id: int):
    """
    Delete an event (연결된 media가 없는 event만 삭제 가능)
    """
    event = query.get_event(db, event_id, user.team_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if query.has_media(db, event_id):
        raise HTTPException(
            status_code=400, detail="Cannot delete event with connected media"
        )

    query.delete_event(db, event)
