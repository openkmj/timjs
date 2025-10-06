from fastapi import APIRouter, HTTPException

from app.db import query as event_db
from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import EventCreate, EventResponse, EventUpdate
from app.utils.push_notification import send_push_notification

router = APIRouter()


@router.get("", response_model=list[EventResponse])
async def get_events(db: DBContext, _: AuthContext):
    """
    Get all events
    """
    events = event_db.get_all_events(db)
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


@router.post("", response_model=EventResponse)
async def create_event(db: DBContext, user: AuthContext, event: EventCreate):
    """
    Create a new event
    """
    new_event = event_db.create_event(
        db=db,
        title=event.title,
        date=event.date,
        description=event.description,
        location=event.location,
        tags=event.tags,
    )

    # Send push notifications to all users except the creator
    users = event_db.list_users(db)
    tokens = [
        u.expo_push_token
        for u in users
        if u.expo_push_token and u.id != user.id
    ]
    send_push_notification(
        tokens=tokens,
        title=new_event.title,
        body=f"{user.name}님이 {new_event.title} 이벤트를 추가했습니다.",
        data={"event_id": new_event.id, "type": "new_event"},
    )

    return EventResponse(
        id=new_event.id,
        title=new_event.title,
        description=new_event.description,
        date=new_event.date,
        location=new_event.location,
        tags=new_event.tags.split(",") if new_event.tags else [],
    )


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    db: DBContext, _: AuthContext, event_id: int, event_update: EventUpdate
):
    """
    Update Event
    """
    event = event_db.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    updated_event = event_db.update_event(
        db=db,
        event=event,
        title=event_update.title,
        date=event_update.date,
        description=event_update.description,
        location=event_update.location,
        tags=event_update.tags,
    )
    return EventResponse(
        id=updated_event.id,
        title=updated_event.title,
        description=updated_event.description,
        date=updated_event.date,
        location=updated_event.location,
        tags=updated_event.tags.split(",") if updated_event.tags else [],
    )


@router.delete("/{event_id}")
async def delete_event(db: DBContext, user: AuthContext, event_id: int):
    """
    Delete an event (연결된 media가 없는 event만 삭제 가능)
    """
    event = event_db.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event_db.has_media(db, event_id):
        raise HTTPException(
            status_code=400, detail="Cannot delete event with connected media"
        )

    event_db.delete_event(db, event)
    return {"message": "Event deleted successfully"}
