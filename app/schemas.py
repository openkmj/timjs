from datetime import datetime

from pydantic import BaseModel


# Event schemas
class EventBase(BaseModel):
    title: str
    description: str | None = None
    date: datetime
    location: str | None = None
    tags: list[str] | None = []


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    date: datetime | None = None
    location: str | None = None
    tags: list[str] | None = None


class EventResponse(EventBase):
    id: int

    class Config:
        from_attributes = True


# Media schemas
class MediaResponse(BaseModel):
    id: int
    event_id: int | None
    user_id: int
    url: str
    thumb_url: str
    file_type: str
    file_size: int | None
    file_metadata: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MediaFeedResponse(BaseModel):
    items: list[MediaResponse]
    cursor: str | None = None
    has_more: bool


class PresignedUploadRequest(BaseModel):
    file_name: str
    content_type: str
    event_id: int | None = None


class PresignedUploadResponse(BaseModel):
    url: str
    fields: dict
    key: str


class ConfirmUploadRequest(BaseModel):
    key: str
    event_id: int | None = None
    file_size: int
    file_metadata: dict | None = None
