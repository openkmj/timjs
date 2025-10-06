from fastapi import APIRouter

from app.middlewares.auth import AuthContext
from app.middlewares.db import DBContext
from app.schemas import EventCreate, EventResponse, EventUpdate

router = APIRouter()


@router.get("", response_model=list[EventResponse])
async def get_events(db: DBContext, user: AuthContext):
    """
    Get all events
    """
    pass


@router.post("", response_model=EventResponse)
async def create_event(db: DBContext, user: AuthContext, event: EventCreate):
    """
    Create a new event
    """
    pass


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    db: DBContext, user: AuthContext, event_id: int, event_update: EventUpdate
):
    """
    Update Event
    """
    pass


@router.delete("/{event_id}")
async def delete_event(db: DBContext, user: AuthContext, event_id: int):
    """
    Delete an event (연결된 media가 없는 event만 삭제 가능)
    """
    pass
